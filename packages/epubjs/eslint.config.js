import baseConfig from '../../eslint.config.js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  ...baseConfig,
  {
    files: ['**/*.ts', '**/*.tsx'],
    rules: {
      '@typescript-eslint/ban-types': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
    },
  }
);
