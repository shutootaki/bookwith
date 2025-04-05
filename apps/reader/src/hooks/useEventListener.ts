import { useEffect, useRef } from 'react'

type MayCallable<T> = T | (() => T)
type Maybe<T> = T | undefined | null
type Options = boolean | EventListenerOptions

// ユニオン型を使用して単一の関数シグネチャで実装
export function useEventListener<K extends keyof WindowEventMap>(
  targetOrType: K | MayCallable<Maybe<EventTarget>>,
  listenerOrType: ((this: any, e: WindowEventMap[K]) => void) | keyof any,
  optionsOrListener?: Options | ((e: any) => void),
  maybeOptions?: Options,
): void {
  let target: MayCallable<Maybe<EventTarget>>
  let type: string
  let listener: (e: any) => void
  let options: Options | undefined

  if (typeof targetOrType === 'string') {
    // ウィンドウイベントの場合
    type = targetOrType as string
    listener = listenerOrType as (e: any) => void
    options = optionsOrListener as Options | undefined
    target = globalThis
  } else {
    // ターゲット指定イベントの場合
    target = targetOrType
    type = listenerOrType as string
    listener = optionsOrListener as (e: any) => void
    options = maybeOptions
  }

  const listenerRef = useRef(listener)
  listenerRef.current = listener

  useEffect(() => {
    const _listener = (e: any) => listenerRef.current(e)
    const _target = typeof target === 'function' ? target() : target

    // _targetがnullまたはundefinedでなく、addEventListenerメソッドを持っている場合のみ実行
    if (_target && typeof _target.addEventListener === 'function') {
      _target.addEventListener(type, _listener, options)

      return () => {
        if (_target && typeof _target.removeEventListener === 'function') {
          _target.removeEventListener(type, _listener, options)
        }
      }
    }

    return undefined
  }, [options, target, type])
}
