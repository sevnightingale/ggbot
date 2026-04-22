import 'dotenv/config'
import Fastify from 'fastify'
import { sharedSecretGuard } from './lib/auth.js'
import { registerSetupHlUnified } from './routes/setup-hl-unified.js'
import { registerAuthorizeHlApiWallet } from './routes/authorize-hl-api-wallet.js'
import { registerWithdrawFromHl } from './routes/withdraw-from-hl.js'
import { registerBridgeUsdcToHl } from './routes/bridge-usdc-to-hl.js'
import { registerJoinLeaderboard } from './routes/join-leaderboard.js'
import { registerForumPost } from './routes/forum-post.js'

const PORT = Number(process.env.ACP_NODE_PORT || 3101)
const SHARED_SECRET = process.env.ACP_NODE_SHARED_SECRET

if (!SHARED_SECRET) {
  console.error('ACP_NODE_SHARED_SECRET is required')
  process.exit(1)
}

const app = Fastify({
  logger: {
    level: process.env.LOG_LEVEL || 'info',
  },
})

app.get('/health', async () => ({
  status: 'ok',
  service: 'acp-node',
  version: '0.1.0',
}))

app.register(async (authedScope) => {
  authedScope.addHook('preHandler', sharedSecretGuard(SHARED_SECRET))
  registerSetupHlUnified(authedScope)
  registerAuthorizeHlApiWallet(authedScope)
  registerWithdrawFromHl(authedScope)
  registerBridgeUsdcToHl(authedScope)
  registerJoinLeaderboard(authedScope)
  registerForumPost(authedScope)
})

app.listen({ port: PORT, host: '127.0.0.1' }).then((addr) => {
  app.log.info(`acp-node listening on ${addr}`)
})
