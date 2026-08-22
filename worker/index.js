const WXPUSHER_SEND_URL = "https://wxpusher.zjiecode.com/api/send/message";
const BEIJING_TIME_ZONE = "Asia/Shanghai";

function jsonResponse(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=UTF-8" },
  });
}

function beijingDate(now = new Date()) {
  const fields = new Intl.DateTimeFormat("en-CA", {
    timeZone: BEIJING_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const parts = Object.fromEntries(fields.map(({ type, value }) => [type, value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function previousDate(date) {
  const value = new Date(`${date}T00:00:00.000Z`);
  value.setUTCDate(value.getUTCDate() - 1);
  return value.toISOString().slice(0, 10);
}

async function upstash(env, command, key, value) {
  const url = new URL(`${env.UPSTASH_REDIS_REST_URL.replace(/\/$/, "")}/${command}/${encodeURIComponent(key)}`);
  const options = {
    method: value === undefined ? "GET" : "POST",
    headers: { Authorization: `Bearer ${env.UPSTASH_REDIS_REST_TOKEN}` },
  };
  if (value !== undefined) {
    options.headers["content-type"] = "application/json";
    options.body = JSON.stringify(value);
  }

  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`Upstash ${command} failed with HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload.error) {
    throw new Error(`Upstash ${command} error: ${payload.error}`);
  }
  return payload.result;
}

async function sendWxPusher(env, uid, content) {
  const response = await fetch(WXPUSHER_SEND_URL, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      appToken: env.WXPUSHER_APP_TOKEN,
      content,
      contentType: 1,
      uids: [uid],
      verifyPayType: 0,
    }),
  });
  if (!response.ok) {
    throw new Error(`WxPusher reply failed with HTTP ${response.status}`);
  }
  const payload = await response.json();
  if (payload.code !== 1000) {
    throw new Error(`WxPusher reply rejected: ${payload.msg || "unknown error"}`);
  }
}

async function handleCheckin(env, uid) {
  const key = `checkin:${uid}`;
  const today = beijingDate();
  const existing = await upstash(env, "get", key);
  const record = existing ? JSON.parse(existing) : null;

  if (record?.last_checkin === today) {
    await sendWxPusher(env, uid, `✅ 今天已经打过卡了！你已连续练习 ${record.streak} 天。`);
    return { status: "already_checked_in", streak: record.streak };
  }

  const streak = record?.last_checkin === previousDate(today) ? Number(record.streak || 0) + 1 : 1;
  await upstash(env, "set", key, { last_checkin: today, streak });
  await sendWxPusher(env, uid, `🎉 打卡成功！你已连续练习 ${streak} 天，继续保持！`);
  return { status: "checked_in", streak };
}

export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      if (request.method !== "POST" || url.pathname !== "/webhook") {
        return jsonResponse({ error: "Not found" }, 404);
      }
      if (!env.WEBHOOK_TOKEN || url.searchParams.get("token") !== env.WEBHOOK_TOKEN) {
        return jsonResponse({ error: "Unauthorized" }, 401);
      }

      const payload = await request.json();
      const data = payload?.data || {};
      if (payload.action !== "send_up_cmd") {
        return jsonResponse({ ignored: "unsupported action" });
      }
      if (env.WXPUSHER_APP_ID && String(data.appId) !== String(env.WXPUSHER_APP_ID)) {
        return jsonResponse({ ignored: "unexpected app" });
      }
      if (typeof data.uid !== "string" || !data.uid || typeof data.content !== "string") {
        return jsonResponse({ error: "Invalid WxPusher payload" }, 400);
      }
      if (!data.content.includes("打卡")) {
        return jsonResponse({ ignored: "no check-in keyword" });
      }

      return jsonResponse(await handleCheckin(env, data.uid));
    } catch (error) {
      console.error("Webhook processing failed", error);
      return jsonResponse({ error: "Internal server error" }, 500);
    }
  },
};
