/**
 * Cloudflare Worker - Grok2API 代理
 * 
 * 部署步骤：
 * 1. 登录 Cloudflare Dashboard
 * 2. 进入 Workers & Pages
 * 3. 创建 Worker
 * 4. 粘贴此代码
 * 5. 保存并部署
 * 6. 复制 Worker URL（如：https://your-worker.your-subdomain.workers.dev）
 * 7. 在 Grok2API 配置中设置 base_proxy_url = "https://your-worker.your-subdomain.workers.dev"
 */

// 允许的源（CORS）
const ALLOWED_ORIGINS = ['*'];

// 目标域名 - Grok 官网
const TARGET_HOST = 'grok.com';

export default {
  async fetch(request, env, ctx) {
    // 处理 CORS 预检请求
    if (request.method === 'OPTIONS') {
      return handleCORS(request);
    }

    // 构建目标 URL
    const url = new URL(request.url);
    const targetUrl = new URL(url.pathname + url.search, `https://${TARGET_HOST}`);

    // 复制请求头
    const headers = new Headers(request.headers);
    headers.set('Host', TARGET_HOST);
    headers.delete('Origin');
    headers.delete('Referer');

    // 构建新请求
    const modifiedRequest = new Request(targetUrl, {
      method: request.method,
      headers: headers,
      body: request.body,
    });

    try {
      // 发送请求到目标
      const response = await fetch(modifiedRequest);

      // 复制响应头
      const newHeaders = new Headers(response.headers);
      newHeaders.set('Access-Control-Allow-Origin', '*');
      newHeaders.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      newHeaders.set('Access-Control-Allow-Headers', '*');

      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: newHeaders,
      });
    } catch (error) {
      return new Response(JSON.stringify({
        error: 'Proxy Error',
        message: error.message,
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*',
        },
      });
    }
  },
};

function handleCORS(request) {
  const origin = request.headers.get('Origin') || '*';
  return new Response(null, {
    status: 204,
    headers: {
      'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': '*',
      'Access-Control-Max-Age': '86400',
    },
  });
}
