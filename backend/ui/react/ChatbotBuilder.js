import React, { useState, useCallback, useEffect, memo } from 'react';
import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  applyNodeChanges,
  applyEdgeChanges,
  Handle,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import yaml from 'js-yaml';

// Custom Node Component
const DefaultNode = memo(({ id, data }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label || '');
  const [state, setState] = useState(data.state || '');

  const handleDoubleClick = (e) => {
    e.stopPropagation();
    setIsEditing(true);
  };

  const handleSubmit = () => {
    data.onChange(id, { label, state });
    setIsEditing(false);
  };

  const handleDelete = () => {
    data.onDelete(id);
  };

  return (
    <div 
      className="p-3 border rounded shadow-md bg-white min-w-[150px]" 
      onDoubleClick={handleDoubleClick}
    >
      <Handle 
        type="target" 
        position={Position.Top} 
        style={{ background: '#555' }} 
      />
      
      {isEditing ? (
        <div className="flex flex-col gap-2">
          <input
            type="text"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            className="border p-1 text-sm"
            placeholder="Node Label"
            autoFocus
          />
          <input
            type="text"
            value={state}
            onChange={(e) => setState(e.target.value)}
            className="border p-1 text-sm"
            placeholder="State Name"
          />
          <div className="flex gap-2">
            <button 
              onClick={handleSubmit}
              className="bg-blue-500 text-white px-2 py-1 text-sm rounded"
            >
              Save
            </button>
            <button 
              onClick={handleDelete}
              className="bg-red-500 text-white px-2 py-1 text-sm rounded"
            >
              Delete
            </button>
          </div>
        </div>
      ) : (
        <div>
          <div className="font-bold">{label || 'Unnamed Node'}</div>
          <div className="text-sm text-gray-600">{state || 'No state'}</div>
        </div>
      )}
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        style={{ background: '#555' }} 
      />
    </div>
  );
});

// Define nodeTypes outside the component
const nodeTypes = {
  default: DefaultNode,
};

const ChatbotBuilder = () => {
  const [nodes, setNodes] = useState(() => {
    const savedNodes = localStorage.getItem('nodes');
    return savedNodes
      ? JSON.parse(savedNodes)
      : [
          {
            id: '1',
            type: 'default',  // Match the key in nodeTypes
            data: { 
              label: 'Start',
              state: 'start',
            },
            position: { x: 250, y: 50 },
          },
        ];
  });

  const [edges, setEdges] = useState(() => {
    const savedEdges = localStorage.getItem('edges');
    return savedEdges ? JSON.parse(savedEdges) : [];
  });

  const [yamlOutput, setYamlOutput] = useState('');

  // Update all nodes to include the callback functions
  const updateNodesWithCallbacks = useCallback((currentNodes) => {
    return currentNodes.map(node => ({
      ...node,
      data: {
        ...node.data,
        onChange: handleNodeChange,
        onDelete: handleNodeDelete,
      },
    }));
  }, []);

  useEffect(() => {
    setNodes(prevNodes => updateNodesWithCallbacks(prevNodes));
  }, [updateNodesWithCallbacks]);

  useEffect(() => {
    localStorage.setItem('nodes', JSON.stringify(nodes));
    localStorage.setItem('edges', JSON.stringify(edges));
  }, [nodes, edges]);

  const addNode = useCallback(() => {
    const newNode = {
      id: `node-${Date.now()}`,
      type: 'default',  // Match the key in nodeTypes
      data: { 
        label: 'New Node',
        state: '',
      },
      position: { x: Math.random() * 300 + 50, y: Math.random() * 300 + 50 },
    };

    setNodes(nds => updateNodesWithCallbacks([...nds, newNode]));
  }, [updateNodesWithCallbacks]);

  const handleNodeChange = useCallback((nodeId, newData) => {
    setNodes(nds =>
      nds.map(node => {
        if (node.id === nodeId) {
          return {
            ...node,
            data: {
              ...node.data,
              ...newData,
            },
          };
        }
        return node;
      })
    );
  }, []);

  const handleNodeDelete = useCallback((nodeId) => {
    setNodes(nds => nds.filter(node => node.id !== nodeId));
    setEdges(eds => eds.filter(edge => 
      edge.source !== nodeId && edge.target !== nodeId
    ));
  }, []);

  const onNodesChange = useCallback(
    (changes) => setNodes(nds => applyNodeChanges(changes, nds)),
    []
  );

  const onEdgesChange = useCallback(
    (changes) => setEdges(eds => applyEdgeChanges(changes, eds)),
    []
  );

  const onConnect = useCallback(
    (params) => {
      if (params.source && params.target) {
        setEdges(eds => addEdge({ ...params, animated: true }, eds));
      }
    },
    []
  );

  const generateYAML = () => {
    const yamlObject = {
      bot_name: "ChatbotName",
      version: "1.0",
      author: "AuthorName",
      initialization: [
        { role: "assistant" },
        { context: "You are an assistant that will help users buy products from an e-commerce website." },
        { start_state: "start" },
      ],
      states: nodes.map(node => ({
        id: node.id,
        state: node.data.state || '',
        label: node.data.label || '',
        position: node.position,
      })),
      transitions: edges.map(edge => ({
        from_state: edge.source,
        to_state: edge.target,
      })),
    };
    setYamlOutput(yaml.dump(yamlObject));
  };

  return (
    <div className="flex flex-col h-screen">
      <div className="border-b p-4 flex justify-between items-center bg-white">
        <h1 className="text-xl font-semibold">Chatbot Flow Builder</h1>
        <div className="flex gap-4">
          <button 
            onClick={addNode} 
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Add Node
          </button>
          <button 
            onClick={generateYAML} 
            className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Generate YAML
          </button>
        </div>
      </div>

      <div style={{ flex: 1, minHeight: '500px' }} className="bg-gray-50">
        <ReactFlow
          nodes={updateNodesWithCallbacks(nodes)}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <MiniMap />
          <Controls />
          <Background />
        </ReactFlow>
      </div>

      {yamlOutput && (
        <pre className="p-4 bg-gray-800 text-white overflow-auto h-48">
          {yamlOutput}
        </pre>
      )}
    </div>
  );
};

export default ChatbotBuilder;