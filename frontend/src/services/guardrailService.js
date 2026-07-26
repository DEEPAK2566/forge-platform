import api from './api'

const guardrailService = {
  async create(data)     { return (await api.post('/guardrails/', data)).data     },
  async list()           { return (await api.get('/guardrails/')).data            },
  async get(id)          { return (await api.get(`/guardrails/${id}`)).data       },
  async update(id, data) { return (await api.put(`/guardrails/${id}`, data)).data },
  async remove(id)       { await api.delete(`/guardrails/${id}`)                  },
}

export default guardrailService