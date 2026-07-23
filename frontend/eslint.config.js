import js from '@eslint/js'
import vuePlugin from 'eslint-plugin-vue'
import tsParser from '@typescript-eslint/parser'
import tsPlugin from '@typescript-eslint/eslint-plugin'
import globals from 'globals'
import vueParser from 'vue-eslint-parser'  // 新增

export default [
  js.configs.recommended,

  // Vue 3 推荐配置（适用于 flat 模式）
  ...vuePlugin.configs['flat/recommended'],

  {
    // 针对 .vue 文件单独配置
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,           // 使用 vue-eslint-parser 解析整个 .vue 文件
      parserOptions: {
        parser: tsParser,          // 解析 <script> 中的 TypeScript
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      vue: vuePlugin,              // 确保 vue 插件被注册
    },
    rules: {
      // 覆盖或补充规则
      'vue/multi-word-component-names': 'off',
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-unused-vars': 'off',     // 关闭原规则，使用 TypeScript 版本
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    },
  },

  // 针对 .ts / .js 文件的配置（非 .vue）
  {
    files: ['**/*.{ts,js}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.es2021,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      '@typescript-eslint/no-unused-vars': ['warn', { argsIgnorePattern: '^_' }],
      'no-unused-vars': 'off',
      '@typescript-eslint/no-explicit-any': 'off',
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
    },
  },

  // 忽略文件
  {
    ignores: [
      '**/dist/**',
      '**/node_modules/**',
      '**/.*/**',
      '**/*.min.js',
      '**/*.d.ts',     // 类型声明文件通常不需要 lint
    ],
  },
]
