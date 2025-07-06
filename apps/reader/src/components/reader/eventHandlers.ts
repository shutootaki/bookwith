import { BookTab } from '../../models'

export function handleKeyDown(tab?: BookTab) {
  return (e: KeyboardEvent) => {
    const activeElement = document.activeElement

    if (
      !activeElement ||
      activeElement.matches('input, textarea, select, [contenteditable]')
    ) {
      return
    }

    try {
      switch (e.code) {
        case 'ArrowLeft':
        case 'ArrowUp':
          tab?.prev()
          break
        case 'ArrowRight':
        case 'ArrowDown':
          tab?.next()
          break
        case 'Space':
          e.shiftKey ? tab?.prev() : tab?.next()
          break
      }
    } catch {
      // ignore `rendition is undefined` error
    }
  }
}
