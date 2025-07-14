export const environment = {
  production: true,
  apiUrl: 'https://api.prompt-maestro.com',
  title: 'Prompt Maestro - Migración NSDK',
  version: '1.0.0',
  features: {
    enableAnalytics: true,
    enableDebug: false,
    enableMockData: false
  },
  llm: {
    defaultProvider: 'openai',
    defaultModel: 'gpt-4',
    maxTokens: 4000,
    temperature: 0.7
  },
  vectorStore: {
    defaultType: 'qdrant',
    defaultCollection: 'nsdk_migration',
    defaultEmbeddingModel: 'text-embedding-3-small'
  },
  git: {
    defaultBranch: 'main',
    migrationBranchPrefix: 'migracion'
  }
};