/**
 * Loading store - backward compatibility layer
 *
 * This file re-exports from the new modular structure to maintain
 * backward compatibility with existing imports.
 *
 * @deprecated Consider importing from '@/store/loading' instead
 */

// Re-export everything from the new modular structure
export * from './loading/index'
