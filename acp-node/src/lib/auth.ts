import type { FastifyRequest, FastifyReply } from 'fastify'

export function sharedSecretGuard(expected: string) {
  return async function guard(req: FastifyRequest, reply: FastifyReply) {
    const got = req.headers['x-service-auth']
    if (typeof got !== 'string' || got !== expected) {
      reply.code(401).send({ error: 'unauthorized' })
    }
  }
}
