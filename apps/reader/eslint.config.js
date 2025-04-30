import baseConfig from '../../eslint.config.js';
import tseslint from 'typescript-eslint';
import reactHooksPlugin from 'eslint-plugin-react-hooks';

export default tseslint.config(
  ...baseConfig,
  {
    files: ['**/*.ts', '**/*.tsx'],
    plugins: {
      'react-hooks': reactHooksPlugin,
    },
    rules: {
      '@next/next/no-html-link-for-pages': 'off',
      '@next/next/no-img-element': 'off',
      'react/jsx-key': 'off',
      'react/no-children-prop': 'off',
      'react-hooks/exhaustive-deps': [
        'warn',
        {
          additionalHooks: 'useRecoilCallback|useRecoilTransaction_UNSTABLE',
        },
      ],
    },
  }
);
