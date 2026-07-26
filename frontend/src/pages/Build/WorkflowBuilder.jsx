import { useState, useCallback, useRef, useMemo, memo, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  BackgroundVariant,
} from 'reactflow'
import 'reactflow/dist/style.css'
import {
  ChevronRight, Save, Upload, Search,
  Plus, Play, Info,
} from 'lucide-react'
import agentService     from '../../services/agentService'
import workflowService  from '../../services/workflowService'
import RunWorkflowModal from '../../components/common/RunWorkflowModal'

// ── Execution type definitions ─────────────────────────────────────────────
const EXEC_TYPES = {
  sequential: { label: 'Sequential', color: '#7C3AED', desc: 'Runs after the previous agent finishes'       },
  parallel:   { label: 'Parallel',   color: '#06B6D4', desc: 'Runs at the same time as sibling agents'      },
  branch:     { label: 'Branch',     color: '#F59E0B', desc: 'One agent fans out to multiple agents'        },
  merge:      { label: 'Merge',      color: '#10B981', desc: 'Multiple agents combine into one'             },
  loop:       { label: 'Loop',       color: '#EF4444', desc: 'Cycles back to an earlier node'               },
}

// ── Custom Agent Node — defined OUTSIDE component to prevent re-creation ──
const AgentNode = memo(({ data, selected }) => {
  const exType = data.execution_type || 'sequential'
  const color  = EXEC_TYPES[exType]?.color || '#7C3AED'

  return (
    <div style={{
      background: '#1A1A2E', border: `2px solid ${selected ? color : color + '55'}`,
      borderRadius: '14px', padding: '10px 14px', minWidth: '170px', cursor: 'pointer',
      position: 'relative',
      boxShadow: selected ? `0 0 0 3px ${color}25, 0 4px 24px rgba(0,0,0,0.5)` : '0 2px 8px rgba(0,0,0,0.4)',
      transition: 'box-shadow 0.15s, border-color 0.15s',
    }}>
      <Handle type="target" position={Position.Left} style={{ background: color, width: 10, height: 10, border: '2px solid #0D0D14', left: -6 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div style={{ width: '38px', height: '38px', borderRadius: '10px', flexShrink: 0, background: `${color}18`, border: `1px solid ${color}35`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}>
          {data.avatar_emoji || '🤖'}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontSize: '13px', fontWeight: '500', color: '#F0F0FF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '108px', marginBottom: '4px' }}>
            {data.agent_name}
          </div>
          <span style={{ fontSize: '9px', fontWeight: '600', letterSpacing: '0.5px', textTransform: 'uppercase', padding: '2px 6px', borderRadius: '4px', background: `${color}18`, color, border: `1px solid ${color}35` }}>
            {EXEC_TYPES[exType]?.label}
          </span>
        </div>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: color, width: 10, height: 10, border: '2px solid #0D0D14', right: -6 }} />
    </div>
  )
})

// ── Main component ─────────────────────────────────────────────────────────
export default function WorkflowBuilder() {
  const navigate         = useNavigate()
  const reactFlowWrapper = useRef(null)
  const nodeCounter      = useRef(1)

  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [rfInstance,     setRfInstance]     = useState(null)

  const [workflowName,   setWorkflowName]   = useState('')
  const [isDirty,        setIsDirty]        = useState(false)
  const [saving,         setSaving]         = useState(false)
  const [error,          setError]          = useState('')
  const [showRunModal,   setShowRunModal]   = useState(false)

  const [agents,         setAgents]         = useState([])
  const [agentSearch,    setAgentSearch]    = useState('')
  const [loadingAgents,  setLoadingAgents]  = useState(true)

  const [selectedNodeId, setSelectedNodeId] = useState(null)

  // nodeTypes MUST be memoized — prevents infinite re-render loop
  const nodeTypes = useMemo(() => ({ agentNode: AgentNode }), [])

  useEffect(() => {
    agentService.list()
      .then(data => setAgents(data))
      .catch(() => {})
      .finally(() => setLoadingAgents(false))
  }, [])

  const onConnect = useCallback((connection) => {
    const sourceType = nodes.find(n => n.id === connection.source)?.data?.execution_type
    const edgeColor  = EXEC_TYPES[sourceType]?.color || '#7C3AED'
    setEdges(eds => addEdge({
      ...connection, type: 'smoothstep', animated: true,
      style: { stroke: edgeColor, strokeWidth: 2 },
    }, eds))
    setIsDirty(true)
  }, [nodes, setEdges])

  const onDragOver = useCallback((e) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    if (!rfInstance) return
    const raw = e.dataTransfer.getData('application/forge-agent')
    if (!raw) return
    const agent    = JSON.parse(raw)
    const bounds   = reactFlowWrapper.current.getBoundingClientRect()
    const position = rfInstance.project({ x: e.clientX - bounds.left, y: e.clientY - bounds.top })
    const newNode  = {
      id:   `node_${nodeCounter.current++}`,
      type: 'agentNode',
      position,
      data: { agent_id: agent.id, agent_name: agent.name, avatar_emoji: agent.avatar_emoji || '🤖', execution_type: 'sequential' },
    }
    setNodes(prev => [...prev, newNode])
    setIsDirty(true)
  }, [rfInstance, setNodes])

  const changeExecType = (nodeId, exType) => {
    setNodes(prev => prev.map(n => n.id === nodeId ? { ...n, data: { ...n.data, execution_type: exType } } : n))
    setIsDirty(true)
  }

  const deleteNode = (nodeId) => {
    setNodes(prev => prev.filter(n => n.id !== nodeId))
    setEdges(prev => prev.filter(e => e.source !== nodeId && e.target !== nodeId))
    setSelectedNodeId(null)
    setIsDirty(true)
  }

  const handleSave = async (status = 'draft') => {
    if (!workflowName.trim()) { setError('Workflow name is required.'); return }
    if (nodes.length === 0)   { setError('Add at least one agent to the canvas.'); return }
    setError('')
    setSaving(true)
    try {
      await workflowService.create({ name: workflowName, nodes, edges, status })
      navigate('/myspace')
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save workflow.')
    } finally {
      setSaving(false)
    }
  }

  const filteredAgents = agents.filter(a => a.name.toLowerCase().includes(agentSearch.toLowerCase()))
  const selectedNode   = nodes.find(n => n.id === selectedNodeId)

  const panelStyle = {
    backgroundColor: '#13131F', border: '1px solid #2A2A3D',
    borderRadius: '0', display: 'flex', flexDirection: 'column',
    overflow: 'hidden', height: '100%',
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#0D0D14' }}>

      {/* ── Run modal ──────────────────────────────────────────────── */}
      {showRunModal && (
        <RunWorkflowModal
          nodes={nodes}
          workflowName={workflowName || 'Untitled Workflow'}
          onCancel={() => setShowRunModal(false)}
          onConfirm={async (input) => {
            setShowRunModal(false)
            if (!workflowName.trim()) { setError('Enter a workflow name before running.'); return }
            if (nodes.length === 0)   { setError('Add at least one agent before running.'); return }
            setError('')
            setSaving(true)
            try {
              const saved = await workflowService.create({ name: workflowName, nodes, edges, status: 'published' })
              const { default: executionService } = await import('../../services/executionService')
              const execution = await executionService.run(saved.id, input)
              navigate(`/executions/${execution.id}`)
            } catch (err) {
              setError(err.response?.data?.detail || 'Failed to start execution.')
              setSaving(false)
            }
          }}
        />
      )}

      {/* ── Top Bar ─────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 24px', height: '52px', borderBottom: '1px solid #2A2A3D', backgroundColor: '#0D0D14', flexShrink: 0, gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: '#5A5A7A', flexShrink: 0 }}>
          <Link to="/myspace" style={{ color: '#5A5A7A', textDecoration: 'none' }}>FORGE</Link>
          <ChevronRight size={13} />
          <span>Build</span>
          <ChevronRight size={13} />
          <span style={{ color: '#F0F0FF', fontWeight: '500' }}>Workflow</span>
        </div>

        <input
          type="text" value={workflowName}
          onChange={e => { setWorkflowName(e.target.value); setIsDirty(true) }}
          placeholder="Enter workflow name..."
          style={{ flex: 1, maxWidth: '400px', backgroundColor: '#1A1A2E', border: '1px solid #2A2A3D', borderRadius: '8px', padding: '6px 12px', color: '#F0F0FF', fontSize: '14px', fontWeight: '500' }}
          onFocus={e => e.target.style.borderColor = '#7C3AED'}
          onBlur={e  => e.target.style.borderColor = '#2A2A3D'}
        />

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {error && <span style={{ fontSize: '12px', color: '#EF4444', maxWidth: '200px' }}>{error}</span>}
          <span style={{ fontSize: '12px', color: '#5A5A7A' }}>
            {nodes.length} agent{nodes.length !== 1 ? 's' : ''} · {edges.length} connection{edges.length !== 1 ? 's' : ''}
          </span>

          {/* Run button — opens RunWorkflowModal */}
          <button
            onClick={() => setShowRunModal(true)}
            style={{ padding: '7px 14px', borderRadius: '8px', fontSize: '13px', fontWeight: '500', backgroundColor: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)', color: '#10B981', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
          >
            <Play size={12} fill="#10B981" /> Run
          </button>

          <button onClick={() => handleSave('draft')} disabled={saving} style={{ padding: '7px 14px', borderRadius: '8px', fontSize: '13px', backgroundColor: 'transparent', border: '1px solid #2A2A3D', color: '#F0F0FF', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Save size={13} /> Save Draft
          </button>

          <button onClick={() => handleSave('published')} disabled={saving} style={{ padding: '7px 14px', borderRadius: '8px', fontSize: '13px', fontWeight: '600', background: saving ? '#2A2A3D' : 'linear-gradient(135deg, #7C3AED, #8B5CF6)', border: 'none', color: 'white', cursor: 'pointer', boxShadow: saving ? 'none' : '0 0 16px rgba(124,58,237,0.3)', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Upload size={13} /> {saving ? 'Saving...' : 'Save & Publish'}
          </button>
        </div>
      </div>

      {/* ── Three-column layout ──────────────────────────────────────── */}
      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>

        {/* LEFT — Agent Selector */}
        <div style={{ ...panelStyle, width: '260px', flexShrink: 0, borderRight: '1px solid #2A2A3D' }}>
          <div style={{ padding: '12px 16px', borderBottom: '1px solid #2A2A3D', backgroundColor: '#1A1A2E', flexShrink: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '10px' }}>
              <span style={{ fontSize: '14px' }}>🤖</span>
              <span style={{ fontSize: '13px', fontWeight: '600', color: '#F0F0FF' }}>Select Agent</span>
            </div>
            <div style={{ position: 'relative' }}>
              <Search size={13} color="#5A5A7A" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', pointerEvents: 'none' }} />
              <input type="text" value={agentSearch} onChange={e => setAgentSearch(e.target.value)} placeholder="Search agents..." style={{ width: '100%', backgroundColor: '#0D0D14', border: '1px solid #2A2A3D', borderRadius: '8px', padding: '7px 10px 7px 30px', color: '#F0F0FF', fontSize: '12px' }} onFocus={e => e.target.style.borderColor = '#7C3AED'} onBlur={e => e.target.style.borderColor = '#2A2A3D'} />
            </div>
          </div>

          <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
            {loadingAgents ? (
              <p style={{ color: '#5A5A7A', fontSize: '12px', textAlign: 'center', padding: '20px 0' }}>Loading agents...</p>
            ) : filteredAgents.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '24px 16px' }}>
                <p style={{ color: '#5A5A7A', fontSize: '12px', lineHeight: '1.6' }}>
                  {agents.length === 0 ? 'No agents yet. Create one first.' : 'No agents match your search.'}
                </p>
              </div>
            ) : (
              filteredAgents.map(agent => (
                <div
                  key={agent.id}
                  draggable
                  onDragStart={(e) => {
                    e.dataTransfer.setData('application/forge-agent', JSON.stringify({ id: agent.id, name: agent.name, avatar_emoji: agent.avatar_emoji || '🤖' }))
                    e.dataTransfer.effectAllowed = 'move'
                  }}
                  style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '8px 10px', borderRadius: '10px', marginBottom: '5px', cursor: 'grab', backgroundColor: '#1A1A2E', border: '1px solid #2A2A3D', transition: 'all 0.15s', userSelect: 'none' }}
                  onMouseEnter={e => { e.currentTarget.style.borderColor = '#7C3AED'; e.currentTarget.style.backgroundColor = 'rgba(124,58,237,0.08)' }}
                  onMouseLeave={e => { e.currentTarget.style.borderColor = '#2A2A3D'; e.currentTarget.style.backgroundColor = '#1A1A2E' }}
                >
                  <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(124,58,237,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '17px', flexShrink: 0 }}>
                    {agent.avatar_emoji || '🤖'}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: '12px', fontWeight: '500', color: '#F0F0FF', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{agent.name}</div>
                    {agent.role && <div style={{ fontSize: '10px', color: '#5A5A7A', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{agent.role}</div>}
                  </div>
                  <div style={{ color: '#2A2A3D', fontSize: '12px', flexShrink: 0 }}>⠿</div>
                </div>
              ))
            )}
          </div>

          <div style={{ padding: '10px', borderTop: '1px solid #2A2A3D', flexShrink: 0 }}>
            <button onClick={() => navigate('/build/agent')} style={{ width: '100%', padding: '8px', borderRadius: '8px', cursor: 'pointer', backgroundColor: 'transparent', border: '1px dashed #2A2A3D', color: '#5A5A7A', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
              <Plus size={12} /> Create New Agent
            </button>
          </div>
        </div>

        {/* CENTER — React Flow Canvas */}
        <div ref={reactFlowWrapper} style={{ flex: 1, position: 'relative' }}>
          <ReactFlow
            nodes={nodes} edges={edges}
            onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
            onConnect={onConnect} onInit={setRfInstance}
            onDrop={onDrop} onDragOver={onDragOver}
            onNodeClick={(e, node) => setSelectedNodeId(node.id)}
            onPaneClick={() => setSelectedNodeId(null)}
            nodeTypes={nodeTypes}
            fitView deleteKeyCode="Delete"
            snapToGrid snapGrid={[16, 16]}
            defaultEdgeOptions={{ type: 'smoothstep', animated: true, style: { stroke: '#7C3AED', strokeWidth: 2 } }}
          >
            <Background variant={BackgroundVariant.Dots} gap={20} size={1} color="#2A2A3D" />
            <Controls showInteractive={false} />
            <MiniMap nodeColor={(n) => EXEC_TYPES[n.data?.execution_type]?.color || '#7C3AED'} nodeStrokeWidth={2} zoomable pannable />
          </ReactFlow>

          {nodes.length === 0 && (
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center', pointerEvents: 'none' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px', opacity: 0.3 }}>🔀</div>
              <p style={{ color: '#5A5A7A', fontSize: '14px', fontWeight: '500', marginBottom: '6px' }}>Drag agents onto the canvas</p>
              <p style={{ color: '#3A3A5A', fontSize: '12px' }}>Connect them to build your workflow</p>
            </div>
          )}
        </div>

        {/* RIGHT — Node Config or Legend */}
        <div style={{ ...panelStyle, width: '240px', flexShrink: 0, borderLeft: '1px solid #2A2A3D' }}>

          {selectedNode ? (
            <>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #2A2A3D', backgroundColor: '#1A1A2E', flexShrink: 0 }}>
                <div style={{ fontSize: '13px', fontWeight: '600', color: '#F0F0FF', marginBottom: '2px' }}>{selectedNode.data.avatar_emoji} {selectedNode.data.agent_name}</div>
                <div style={{ fontSize: '11px', color: '#5A5A7A' }}>Click an execution type below</div>
              </div>

              <div style={{ padding: '12px', overflowY: 'auto', flex: 1 }}>
                <p style={{ fontSize: '11px', color: '#5A5A7A', marginBottom: '10px', fontWeight: '500', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Execution Type</p>

                {Object.entries(EXEC_TYPES).map(([key, info]) => {
                  const isActive = selectedNode.data.execution_type === key
                  return (
                    <button key={key} onClick={() => changeExecType(selectedNode.id, key)} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', width: '100%', padding: '9px 10px', borderRadius: '9px', marginBottom: '5px', cursor: 'pointer', textAlign: 'left', backgroundColor: isActive ? `${info.color}15` : 'transparent', border: `1px solid ${isActive ? info.color + '50' : '#2A2A3D'}`, transition: 'all 0.15s' }}
                      onMouseEnter={e => { if (!isActive) { e.currentTarget.style.borderColor = info.color + '40'; e.currentTarget.style.backgroundColor = info.color + '0A' } }}
                      onMouseLeave={e => { if (!isActive) { e.currentTarget.style.borderColor = '#2A2A3D'; e.currentTarget.style.backgroundColor = 'transparent' } }}
                    >
                      <div style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: isActive ? info.color : 'transparent', border: `2px solid ${isActive ? info.color : '#2A2A3D'}`, flexShrink: 0, marginTop: '2px', transition: 'all 0.15s' }} />
                      <div>
                        <div style={{ fontSize: '12px', fontWeight: '500', color: isActive ? info.color : '#8B8BB3', marginBottom: '1px' }}>{info.label}</div>
                        <div style={{ fontSize: '10px', color: '#5A5A7A', lineHeight: '1.4' }}>{info.desc}</div>
                      </div>
                    </button>
                  )
                })}

                <div style={{ borderTop: '1px solid #2A2A3D', marginTop: '12px', paddingTop: '12px' }}>
                  <button onClick={() => deleteNode(selectedNode.id)} style={{ width: '100%', padding: '8px', borderRadius: '8px', cursor: 'pointer', backgroundColor: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.25)', color: '#EF4444', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
                    Remove node
                  </button>
                </div>
              </div>
            </>
          ) : (
            <>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid #2A2A3D', backgroundColor: '#1A1A2E', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
                  <Info size={13} color="#5A5A7A" />
                  <span style={{ fontSize: '13px', fontWeight: '600', color: '#F0F0FF' }}>Execution Modes</span>
                </div>
              </div>

              <div style={{ padding: '12px', overflowY: 'auto', flex: 1 }}>
                {Object.entries(EXEC_TYPES).map(([key, info]) => (
                  <div key={key} style={{ padding: '9px 10px', borderRadius: '9px', marginBottom: '5px', border: '1px solid #2A2A3D', backgroundColor: '#1A1A2E' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '7px', marginBottom: '3px' }}>
                      <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: info.color, flexShrink: 0 }} />
                      <span style={{ fontSize: '12px', fontWeight: '500', color: info.color }}>{info.label}</span>
                    </div>
                    <p style={{ fontSize: '11px', color: '#5A5A7A', lineHeight: '1.5', paddingLeft: '17px' }}>{info.desc}</p>
                  </div>
                ))}

                <div style={{ padding: '10px', borderRadius: '9px', marginTop: '8px', backgroundColor: '#1A1A2E', border: '1px solid #2A2A3D' }}>
                  <p style={{ fontSize: '11px', color: '#5A5A7A', lineHeight: '1.6' }}>
                    <span style={{ color: '#8B8BB3', fontWeight: '500' }}>Tip:</span> Drag agents from the left onto the canvas. Connect by dragging from one node's right handle to another's left handle.
                  </p>
                </div>

                <div style={{ padding: '10px', borderRadius: '9px', marginTop: '6px', backgroundColor: '#1A1A2E', border: '1px solid #2A2A3D' }}>
                  <p style={{ fontSize: '11px', color: '#5A5A7A', lineHeight: '1.6' }}>
                    <span style={{ color: '#8B8BB3', fontWeight: '500' }}>Variables:</span> Use <span style={{ color: '#A78BFA', fontFamily: 'monospace' }}>{'{{ var_name }}'}</span> in agent descriptions to create dynamic input fields when running.
                  </p>
                </div>

                <div style={{ padding: '10px', borderRadius: '9px', marginTop: '6px', backgroundColor: '#1A1A2E', border: '1px solid #2A2A3D' }}>
                  <p style={{ fontSize: '11px', color: '#5A5A7A', lineHeight: '1.6' }}>
                    <span style={{ color: '#8B8BB3', fontWeight: '500' }}>Delete:</span> Select a node and press the Delete key, or click the node and use the Remove button.
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}