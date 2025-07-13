declare global {
  interface Window {
    podcastSeekFunction?: (time: number) => void
  }
}

export {}
