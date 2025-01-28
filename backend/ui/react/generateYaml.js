import yaml from 'js-yaml';

export const generateYAML = (nodes) => {
  return yaml.dump({
    bot_name: "ChatbotName",
    version: "1.0",
    author: "AuthorName",
    initialization: [
      { role: "assistant" },
      { context: "You are an assistant that will help users buy products from an e-commerce website." },
      { start_state: "start" },
    ],
    states: nodes.map((node) => ({
      state: node.data.state,
      trigger: node.data.trigger,
      goal: node.data.goal,
      tools_available: node.data.tools_available,
      actions_available: node.data.actions_available,
      states_available: node.data.states_available,
    })),
  });
};