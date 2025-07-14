export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000',
  title: 'Prompt Maestro - Migración NSDK',
  version: '1.0.0',
  features: {
    enableAnalytics: false,
    enableDebug: true,
    enableMockData: true
  },
  llm: {
    defaultProvider: 'openai',
    defaultModel: 'gpt-4',
    maxTokens: 4000,
    temperature: 0.7
  },
  vectorStore: {
    defaultType: 'faiss',
    defaultCollection: 'nsdk_migration',
    defaultEmbeddingModel: 'text-embedding-3-small'
  },
  git: {
    defaultBranch: 'main',
    migrationBranchPrefix: 'migracion'
  }
};