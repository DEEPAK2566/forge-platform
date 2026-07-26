import api from './api'

const executionService = {

  // POST /executions/run/{workflow_id}?user_input=...
  // Starts a workflow run, returns execution object with id
  async run(workflowId, userInput = '') {
    const response = await api.post(
      `/executions/run/${workflowId}`,
      null,  // no body
      { params: { user_input: userInput } }
    )
    return response.data
  },

  // GET /executions/ — recent executions for the dashboard
  async list(limit = 20) {
    const response = await api.get('/executions/', { params: { limit } })
    return response.data
  },

  // GET /executions/{id} — full execution with logs (used for polling)
  async get(id) {
    const response = await api.get(`/executions/${id}`)
    return response.data
  },

  // GET /executions/workflow/{workflow_id} — runs for a specific workflow
  async getByWorkflow(workflowId) {
    const response = await api.get(`/executions/workflow/${workflowId}`)
    return response.data
  },
}

export default executionService