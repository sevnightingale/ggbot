22:38:03.697 Running build in Portland, USA (West) – pdx1
22:38:03.698 Build machine configuration: 2 cores, 8 GB
22:38:03.814 Cloning github.com/sevnightingale/ggbot (Branch: main, Commit: 1a2f42c)
22:38:05.924 Cloning completed: 2.110s
22:38:06.175 Restored build cache from previous deployment (2B42BP93rGAnYT6EYGi84sTwMvUR)
22:38:06.532 Running "vercel build"
22:38:07.059 Vercel CLI 50.15.1
22:38:07.362 Running "install" command: `npm install`...
22:38:09.220 npm warn ERESOLVE overriding peer dependency
22:38:09.221 npm warn While resolving: use-sync-external-store@1.2.0
22:38:09.221 npm warn Found: react@19.1.0
22:38:09.222 npm warn node_modules/react
22:38:09.222 npm warn   react@"^19.0.0" from the root project
22:38:09.222 npm warn   68 more (zustand, zustand, @mdx-js/react, ...)
22:38:09.222 npm warn
22:38:09.223 npm warn Could not resolve dependency:
22:38:09.223 npm warn peer react@"^16.8.0 || ^17.0.0 || ^18.0.0" from use-sync-external-store@1.2.0
22:38:09.223 npm warn node_modules/valtio/node_modules/use-sync-external-store
22:38:09.224 npm warn   use-sync-external-store@"1.2.0" from valtio@1.13.2
22:38:09.224 npm warn   node_modules/valtio
22:38:09.224 npm warn
22:38:09.224 npm warn Conflicting peer dependency: react@18.3.1
22:38:09.225 npm warn node_modules/react
22:38:09.225 npm warn   peer react@"^16.8.0 || ^17.0.0 || ^18.0.0" from use-sync-external-store@1.2.0
22:38:09.225 npm warn   node_modules/valtio/node_modules/use-sync-external-store
22:38:09.225 npm warn     use-sync-external-store@"1.2.0" from valtio@1.13.2
22:38:09.225 npm warn     node_modules/valtio
22:38:09.966 
22:38:09.967 up to date, audited 1197 packages in 2s
22:38:09.967 
22:38:09.967 359 packages are looking for funding
22:38:09.968   run `npm fund` for details
22:38:09.969 
22:38:09.969 2 high severity vulnerabilities
22:38:09.970 
22:38:09.970 To address all issues, run:
22:38:09.970   npm audit fix
22:38:09.970 
22:38:09.970 Run `npm audit` for details.
22:38:10.001 Detected Next.js version: 15.5.11
22:38:10.002 Running "npm run build"
22:38:10.117 
22:38:10.117 > ggbot-app@0.1.0 build
22:38:10.117 > next build
22:38:10.118 
22:38:11.056  ⚠ Mismatching @next/swc version, detected: 15.5.7 while Next.js is on 15.5.11. Please ensure these match
22:38:11.231    ▲ Next.js 15.5.11
22:38:11.232 
22:38:11.332    Creating an optimized production build ...
22:38:12.127  ⚠ Mismatching @next/swc version, detected: 15.5.7 while Next.js is on 15.5.11. Please ensure these match
22:38:26.053  ⚠ Compiled with warnings in 13.7s
22:38:26.054 
22:38:26.054 ./node_modules/@metamask/sdk/dist/browser/es/metamask-sdk.js
22:38:26.054 Module not found: Can't resolve '@react-native-async-storage/async-storage' in '/vercel/path0/frontend/node_modules/@metamask/sdk/dist/browser/es'
22:38:26.054 
22:38:26.054 Import trace for requested module:
22:38:26.054 ./node_modules/@metamask/sdk/dist/browser/es/metamask-sdk.js
22:38:26.054 ./node_modules/@wagmi/connectors/dist/esm/metaMask.js
22:38:26.054 ./node_modules/@wagmi/connectors/dist/esm/exports/index.js
22:38:26.055 ./node_modules/wagmi/dist/esm/exports/connectors.js
22:38:26.055 ./node_modules/@rainbow-me/rainbowkit/dist/index.js
22:38:26.055 ./components/hyperliquid/HyperliquidSetup.tsx
22:38:26.055 ./app/hyperliquid/page.tsx
22:38:26.055 
22:38:26.055 ./node_modules/pino/lib/tools.js
22:38:26.055 Module not found: Can't resolve 'pino-pretty' in '/vercel/path0/frontend/node_modules/pino/lib'
22:38:26.055 
22:38:26.055 Import trace for requested module:
22:38:26.056 ./node_modules/pino/lib/tools.js
22:38:26.056 ./node_modules/pino/pino.js
22:38:26.056 ./node_modules/@walletconnect/logger/dist/index.es.js
22:38:26.056 ./node_modules/@walletconnect/universal-provider/dist/index.es.js
22:38:26.056 ./node_modules/@walletconnect/ethereum-provider/dist/index.es.js
22:38:26.056 ./node_modules/@wagmi/connectors/dist/esm/walletConnect.js
22:38:26.056 ./node_modules/@wagmi/connectors/dist/esm/exports/index.js
22:38:26.056 ./node_modules/wagmi/dist/esm/exports/connectors.js
22:38:26.056 ./node_modules/@rainbow-me/rainbowkit/dist/index.js
22:38:26.056 ./components/hyperliquid/HyperliquidSetup.tsx
22:38:26.056 ./app/hyperliquid/page.tsx
22:38:26.056 
22:38:26.781  ⚠ Mismatching @next/swc version, detected: 15.5.7 while Next.js is on 15.5.11. Please ensure these match
22:38:27.939  ⚠ Mismatching @next/swc version, detected: 15.5.7 while Next.js is on 15.5.11. Please ensure these match
22:38:30.807 Browserslist: browsers data (caniuse-lite) is 9 months old. Please run:
22:38:30.808   npx update-browserslist-db@latest
22:38:30.808   Why you should do it regularly: https://github.com/browserslist/update-db#readme
22:38:40.425  ⚠ Compiled with warnings in 12.3s
22:38:40.426 
22:38:40.426 ./node_modules/@metamask/sdk/dist/browser/es/metamask-sdk.js
22:38:40.427 Module not found: Can't resolve '@react-native-async-storage/async-storage' in '/vercel/path0/frontend/node_modules/@metamask/sdk/dist/browser/es'
22:38:40.427 
22:38:40.427 Import trace for requested module:
22:38:40.427 ./node_modules/@metamask/sdk/dist/browser/es/metamask-sdk.js
22:38:40.427 ./node_modules/@wagmi/connectors/dist/esm/metaMask.js
22:38:40.428 ./node_modules/@wagmi/connectors/dist/esm/exports/index.js
22:38:40.428 ./node_modules/wagmi/dist/esm/exports/connectors.js
22:38:40.433 ./node_modules/@rainbow-me/rainbowkit/dist/index.js
22:38:40.434 ./components/hyperliquid/HyperliquidSetup.tsx
22:38:40.434 ./app/hyperliquid/page.tsx
22:38:40.434 
22:38:40.485  ✓ Compiled successfully in 26.4s
22:38:40.490    Linting and checking validity of types ...
22:38:51.666 
22:38:51.666 ./app/admin/bots-comparison/page.tsx
22:38:51.667 259:21  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.667 
22:38:51.670 ./components/BotImageUpload.tsx
22:38:51.670 173:6  Warning: React Hook useCallback has a missing dependency: 'handleUpload'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
22:38:51.670 243:11  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.670 
22:38:51.670 ./components/UpgradeModal.tsx
22:38:51.670 128:6  Warning: React Hook useMemo has a missing dependency: 'FREQUENCY_LABELS'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
22:38:51.670 
22:38:51.670 ./components/arena/ArenaWithStaking.tsx
22:38:51.671 263:13  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.671 415:31  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.671 529:31  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.671 
22:38:51.671 ./components/arena/BetModal.tsx
22:38:51.671 316:15  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.671 
22:38:51.671 ./components/hyperliquid/HyperliquidSetup.tsx
22:38:51.671 732:19  Warning: Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` or a custom image loader to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
22:38:51.671 
22:38:51.672 info  - Need to disable some ESLint rules? Learn more here: https://nextjs.org/docs/app/api-reference/config/eslint#disabling-rules
22:39:02.834    Collecting page data ...
22:39:07.023    Generating static pages (0/33) ...
22:39:07.856    Generating static pages (8/33) 
22:39:08.549    Generating static pages (16/33) 
22:39:08.549    Generating static pages (24/33) 
22:39:09.797  ✓ Generating static pages (33/33)
22:39:10.068    Finalizing page optimization ...
22:39:10.076    Collecting build traces ...
22:39:17.035 
22:39:17.044 Route (app)                                          Size  First Load JS
22:39:17.044 ┌ ○ /                                               153 B         105 kB
22:39:17.045 ├ ○ /_not-found                                      1 kB         106 kB
22:39:17.045 ├ ƒ /admin                                        4.54 kB         157 kB
22:39:17.045 ├ ƒ /admin/bots-comparison                         107 kB         259 kB
22:39:17.045 ├ ƒ /admin/users                                  2.91 kB         156 kB
22:39:17.045 ├ ƒ /admin/users/[user_id]                        5.18 kB         158 kB
22:39:17.045 ├ ○ /arena                                        2.46 kB         108 kB
22:39:17.045 ├ ○ /arena/icon.png                                   0 B            0 B
22:39:17.045 ├ ○ /arena/opengraph-image.png                        0 B            0 B
22:39:17.045 ├ ƒ /auth/callback                                  153 B         105 kB
22:39:17.045 ├ ○ /blog                                           176 B         109 kB
22:39:17.045 ├ ● /blog/[slug]                                    176 B         109 kB
22:39:17.045 ├   ├ /blog/ai-confidence-scores-position-sizing
22:39:17.046 ├   ├ /blog/trading-bots-vs-ai-agents-2026
22:39:17.046 ├   └ /blog/what-is-vibe-trading
22:39:17.046 ├ ○ /credits/success                              1.83 kB         107 kB
22:39:17.046 ├ ƒ /feed.xml                                       153 B         105 kB
22:39:17.046 ├ ƒ /forge                                        69.9 kB         356 kB
22:39:17.046 ├ ○ /hyperliquid                                  2.33 kB         107 kB
22:39:17.046 ├ ○ /icon.png                                         0 B            0 B
22:39:17.046 ├ ○ /landing                                      8.04 kB         123 kB
22:39:17.046 ├ ○ /login                                        1.69 kB         171 kB
22:39:17.046 ├ ○ /opengraph-image.png                              0 B            0 B
22:39:17.046 ├ ○ /privacy                                      3.14 kB         108 kB
22:39:17.046 ├ ○ /robots.txt                                     153 B         105 kB
22:39:17.046 ├ ○ /settings                                       352 B         105 kB
22:39:17.046 ├ ○ /settings/api-keys                              384 B         105 kB
22:39:17.046 ├ ○ /signup                                       1.83 kB         171 kB
22:39:17.046 ├ ○ /sitemap.xml                                    153 B         105 kB
22:39:17.046 ├ ○ /success                                      1.94 kB         107 kB
22:39:17.046 ├ ○ /terms                                        5.11 kB         110 kB
22:39:17.046 ├ ○ /test                                         3.38 kB         153 kB
22:39:17.047 ├ ○ /twitter-image.png                                0 B            0 B
22:39:17.047 └ ƒ /view/[config_id]                             6.86 kB         278 kB
22:39:17.047 + First Load JS shared by all                      105 kB
22:39:17.047   ├ chunks/1255-7999eac54f80a49f.js               45.7 kB
22:39:17.047   ├ chunks/4bd1b696-100b9d70ed4e49c1.js           54.2 kB
22:39:17.047   └ other shared chunks (total)                   5.14 kB
22:39:17.047 
22:39:17.047 
22:39:17.047 ƒ Middleware                                        34 kB
22:39:17.047 
22:39:17.047 ○  (Static)   prerendered as static content
22:39:17.047 ●  (SSG)      prerendered as static HTML (uses generateStaticParams)
22:39:17.047 ƒ  (Dynamic)  server-rendered on demand
22:39:17.047 
22:39:17.203 Traced Next.js server files in: 41.601ms
22:39:17.566 WARNING: Unable to find source file for page /arena/icon.png/route with extensions: tsx, ts, jsx, js, this can cause functions config from `vercel.json` to not be applied
22:39:17.567 WARNING: Unable to find source file for page /arena/opengraph-image.png/route with extensions: tsx, ts, jsx, js, this can cause functions config from `vercel.json` to not be applied
22:39:17.624 Created all serverless functions in: 421.308ms
22:39:17.704 Collected static files (public/, static/, .next/static): 24.361ms
22:39:18.051 Build Completed in /vercel/output [1m]
22:39:18.431 Error: Vulnerable version of next-mdx-remote detected (5.0.0). Please update to version 6.0.0 or later. Learn More: https://vercel.link/CVE-2026-0969