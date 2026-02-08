import fastify from 'fastify';
import { buildApp } from '../src/app.js';

const POSTMAN_API = 'https://api.postman.com';

interface RouteInfo {
  method: string;
  url: string;
}

interface PostmanItem {
  name: string;
  request?: {
    method: string;
    header: never[];
    url: {
      raw: string;
      host: string[];
      path: string[];
    };
  };
  item?: PostmanItem[];
}

// ── Route Collection ────────────────────────────────────────────────

function collectRoutes(): Promise<{ routes: RouteInfo[]; cleanup: () => Promise<void> }> {
  const routes: RouteInfo[] = [];

  return (async () => {
    const app = fastify({ logger: false });

    app.addHook('onRoute', (routeOptions) => {
      const methods = Array.isArray(routeOptions.method)
        ? routeOptions.method
        : [routeOptions.method];

      for (const method of methods) {
        if (['GET', 'POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
          routes.push({ method, url: routeOptions.url });
        }
      }
    });

    await buildApp(app);
    await app.ready();

    return { routes, cleanup: () => app.close() };
  })();
}

// ── Postman Collection Builder ──────────────────────────────────────

function groupRoutesByPrefix(routes: RouteInfo[]): Map<string, RouteInfo[]> {
  const groups = new Map<string, RouteInfo[]>();

  for (const route of routes) {
    const segments = route.url.split('/').filter(Boolean);
    const prefix = segments[0] ?? 'root';

    if (!groups.has(prefix)) {
      groups.set(prefix, []);
    }
    groups.get(prefix)!.push(route);
  }

  return groups;
}

function buildPostmanCollection(routes: RouteInfo[]) {
  const groups = groupRoutesByPrefix(routes);
  const folders: PostmanItem[] = [];

  for (const [prefix, groupRoutes] of groups) {
    const items: PostmanItem[] = groupRoutes.map((route) => ({
      name: `${route.method} ${route.url}`,
      request: {
        method: route.method,
        header: [],
        url: {
          raw: `{{baseUrl}}${route.url}`,
          host: ['{{baseUrl}}'],
          path: route.url.split('/').filter(Boolean),
        },
      },
    }));

    folders.push({ name: prefix, item: items });
  }

  return {
    info: {
      name: 'Portal API',
      schema: 'https://schema.getpostman.com/json/collection/v2.1.0/collection.json',
    },
    item: folders,
    variable: [{ key: 'baseUrl', value: 'http://localhost:3000' }],
  };
}

// ── Postman API ─────────────────────────────────────────────────────

async function postmanFetch(path: string, apiKey: string, options?: RequestInit) {
  const res = await fetch(`${POSTMAN_API}${path}`, {
    ...options,
    headers: {
      'X-Api-Key': apiKey,
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(`Postman API ${res.status}: ${body}`);
  }

  return res.json();
}

async function findExistingCollection(
  apiKey: string,
  workspaceId: string,
): Promise<string | null> {
  const data = await postmanFetch(
    `/collections?workspace=${workspaceId}`,
    apiKey,
  );

  const match = data.collections?.find(
    (c: { name: string }) => c.name === 'Portal API',
  );

  return match?.uid ?? null;
}

async function syncToPostman(
  collection: ReturnType<typeof buildPostmanCollection>,
  apiKey: string,
  workspaceId: string,
) {
  const existingId = await findExistingCollection(apiKey, workspaceId);

  if (existingId) {
    await postmanFetch(`/collections/${existingId}`, apiKey, {
      method: 'PUT',
      body: JSON.stringify({ collection }),
    });
    console.log(`Updated Postman collection: ${existingId}`);
  } else {
    const data = await postmanFetch(
      `/collections?workspace=${workspaceId}`,
      apiKey,
      {
        method: 'POST',
        body: JSON.stringify({ collection }),
      },
    );
    console.log(`Created Postman collection: ${data.collection?.uid}`);
  }
}

// ── Main ────────────────────────────────────────────────────────────

async function main() {
  // collectRoutes() triggers buildApp() which loads .env via dotenv,
  // so POSTMAN_API_KEY and POSTMAN_WORKSPACE_ID become available after this call.
  const { routes, cleanup } = await collectRoutes();

  try {
    const apiKey = process.env.POSTMAN_API_KEY;
    const workspaceId = process.env.POSTMAN_WORKSPACE_ID;

    if (!apiKey || !workspaceId) {
      console.warn(
        'Skipping Postman sync: POSTMAN_API_KEY or POSTMAN_WORKSPACE_ID not set',
      );
      return;
    }

    console.log(`Discovered ${routes.length} routes`);
    const collection = buildPostmanCollection(routes);
    await syncToPostman(collection, apiKey, workspaceId);
  } finally {
    await cleanup();
  }
}

main().catch((err) => {
  console.error('Postman sync failed:', err.message);
  process.exit(0); // Exit 0 so pre-commit hook doesn't block
});
