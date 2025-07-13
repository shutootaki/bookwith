import { useCallback, useRef } from 'react'

import { AUDIO_CONTROLS } from '../../constants/audio'
import { PODCAST_KEYBOARD_SHORTCUTS } from '../../constants/podcast'
import { seekAudio } from '../../utils/podcast'

interface UseAudioControlsParams {
  audioRef: React.RefObject<HTMLAudioElement | null>
  duration: number
  onTimeUpdate: (time: number) => void
  onPlayPause?: () => void
  onVolumeChange?: (volume: number) => void
  onSpeedChange?: (speed: number) => void
}

interface AudioControls {
  togglePlayPause: () => void
  handleVolumeChange: (volume: number) => void
  handleSpeedChange: (speed: number) => void
  skipBack: () => void
  skipForward: () => void
  handleProgressClick: (event: React.MouseEvent<HTMLDivElement>) => void
}

/**
 * オーディオコントロールのロジックを管理するカスタムフック
 */
export const useAudioControls = ({
  audioRef,
  duration,
  onTimeUpdate,
  onPlayPause,
  onVolumeChange,
  onSpeedChange,
}: UseAudioControlsParams): AudioControls => {
  const isPlayingRef = useRef(false)

  const togglePlayPause = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlayingRef.current) {
      audio.pause()
      isPlayingRef.current = false
    } else {
      audio.play()
      isPlayingRef.current = true
    }
    onPlayPause?.()
  }, [audioRef, onPlayPause])

  const handleVolumeChange = useCallback(
    (volume: number) => {
      const clampedVolume = Math.max(
        AUDIO_CONTROLS.MIN_VOLUME,
        Math.min(AUDIO_CONTROLS.MAX_VOLUME, volume),
      )
      onVolumeChange?.(clampedVolume)
    },
    [onVolumeChange],
  )

  const handleSpeedChange = useCallback(
    (speed: number) => {
      const audio = audioRef.current
      if (!audio) return

      audio.playbackRate = speed
      onSpeedChange?.(speed)
    },
    [audioRef, onSpeedChange],
  )

  const skipBack = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    seekAudio(audio, -AUDIO_CONTROLS.SKIP_SECONDS, duration, onTimeUpdate)
  }, [audioRef, duration, onTimeUpdate])

  const skipForward = useCallback(() => {
    const audio = audioRef.current
    if (!audio) return

    seekAudio(audio, AUDIO_CONTROLS.SKIP_SECONDS, duration, onTimeUpdate)
  }, [audioRef, duration, onTimeUpdate])

  const handleProgressClick = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      const audio = audioRef.current
      if (!audio) return

      const progressBar = event.currentTarget
      const clickX = event.clientX - progressBar.getBoundingClientRect().left
      const width = progressBar.offsetWidth
      const newTime = (clickX / width) * duration
      audio.currentTime = newTime
      onTimeUpdate(newTime)
    },
    [audioRef, duration, onTimeUpdate],
  )

  return {
    togglePlayPause,
    handleVolumeChange,
    handleSpeedChange,
    skipBack,
    skipForward,
    handleProgressClick,
  }
}

/**
 * キーボードショートカットを処理するフック
 */
export const useAudioKeyboardShortcuts = (
  controls: AudioControls,
  audioRef: React.RefObject<HTMLAudioElement | null>,
) => {
  const handleKeyPress = useCallback(
    (event: KeyboardEvent) => {
      const audio = audioRef.current
      if (!audio) return

      switch (event.key) {
        case PODCAST_KEYBOARD_SHORTCUTS.PLAY_PAUSE:
          event.preventDefault()
          controls.togglePlayPause()
          break
        case PODCAST_KEYBOARD_SHORTCUTS.SKIP_BACK:
          controls.skipBack()
          break
        case PODCAST_KEYBOARD_SHORTCUTS.SKIP_FORWARD:
          controls.skipForward()
          break
        case PODCAST_KEYBOARD_SHORTCUTS.VOLUME_UP:
          controls.handleVolumeChange(
            Math.min(audio.volume + AUDIO_CONTROLS.VOLUME_STEP, 1),
          )
          break
        case PODCAST_KEYBOARD_SHORTCUTS.VOLUME_DOWN:
          controls.handleVolumeChange(
            Math.max(audio.volume - AUDIO_CONTROLS.VOLUME_STEP, 0),
          )
          break
        case PODCAST_KEYBOARD_SHORTCUTS.MUTE_TOGGLE:
          controls.handleVolumeChange(audio.volume > 0 ? 0 : 1)
          break
      }
    },
    [controls, audioRef],
  )

  return { handleKeyPress }
}
