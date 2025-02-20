export function keys<T extends object>(o: T) {
  return Object.keys(o) as (keyof T)[]
}

export function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max)
}

export function last<T>(array: T[]) {
  return array[array.length - 1]
}

export function group<T>(array: T[], getKey: (item: T) => string | number) {
  const o: Record<string, T[]> = {}

  array.forEach((item) => {
    const key = getKey(item)
    o[key] = [...(o[key] ?? []), item]
  })

  return o
}

export function copy(text: string) {
  return navigator.clipboard.writeText(text)
}

export function cleanUpText(str: string, strict = false): string {
  str = str.replace(/^\s+|\s+$/g, '')
  if (strict) {
    str = str.replace(/\n{2,}/g, '\n')
  }
  return str
}
