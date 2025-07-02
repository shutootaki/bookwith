import clsx from 'clsx'
import {
  useContext,
  useState,
  createContext,
  DragEvent,
  useCallback,
  useEffect,
  PropsWithChildren,
} from 'react'

interface DropZoneProps {
  className?: string
  onDrop?: (e: DragEvent<HTMLDivElement>, position?: Position) => void
  split?: boolean
}
export const DropZone: React.FC<PropsWithChildren<DropZoneProps>> = (props) => {
  return (
    <DndProvider>
      <DropZoneInner {...props} />
    </DndProvider>
  )
}

type Position = 'universe' | 'left' | 'right' | 'top' | 'bottom'

// > During the drag, in an event listener for the dragenter and dragover events, you use the data types of the data being dragged to check whether a drop is allowed.
// https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/Drag_operations#drag_data
function accept(e?: DragEvent) {
  const dt = e?.dataTransfer
  return !!dt?.types.every((t) => ['text/plain', 'Files'].includes(t))
}

const DropZoneInner: React.FC<PropsWithChildren<DropZoneProps>> = ({
  children,
  className,
  onDrop,
  split = false,
}) => {
  const { dragover, setDragEvent } = useDndContext()
  const [position, setPosition] = useState<Position>()

  useEffect(() => {
    if (!dragover) setPosition(undefined)
  }, [dragover])

  const handleDragover = useCallback(
    (e: DragEvent<HTMLDivElement>) => {
      e.stopPropagation()
      e.preventDefault()

      setPosition(() => {
        if (!split) return 'universe'

        const rect = (e.target as HTMLDivElement).getBoundingClientRect()
        if (!rect.width || !rect.height) return

        const offsetLeft = (e.clientX - rect.left) / rect.width
        const offsetTop = (e.clientY - rect.top) / rect.height
        const offsetRight = 1 - offsetLeft
        const offsetBottom = 1 - offsetTop
        const threshold = 0.15

        // TODO: add `offsetTop` and `offsetBottom`
        const minOffset = Math.min(offsetLeft, offsetRight)

        if (minOffset > threshold) return 'universe'
        if (minOffset === offsetLeft) return 'left'
        if (minOffset === offsetRight) return 'right'
        if (minOffset === offsetTop) return 'top'
        if (minOffset === offsetBottom) return 'bottom'
      })
    },
    [split],
  )

  return (
    <div
      className={clsx('relative', className)}
      // https://developer.mozilla.org/en-US/docs/Web/API/File/Using_files_from_web_applications#selecting_files_using_drag_and_drop
      onDragEnter={(e) => {
        if (dragover) return

        setDragEvent(e)
        e.stopPropagation()
        e.preventDefault()
      }}
    >
      {children}

      {dragover && (
        <div
          className={clsx(
            'absolute z-10 transition-all duration-200',
            position === 'left' && 'inset-y-0 right-1/2 left-0',
            position === 'right' && 'inset-y-0 right-0 left-1/2',
            position === 'top' && 'inset-x-0 top-0 bottom-1/2',
            position === 'bottom' && 'inset-x-0 top-1/2 bottom-0',
            position === 'universe' && 'inset-0',
          )}
        >
          <div className="absolute inset-0 animate-pulse rounded-lg border-2 border-dashed border-blue-500 bg-blue-500/10 backdrop-blur-sm">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="rounded-lg bg-white px-4 py-2 shadow-lg dark:bg-gray-900">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  ドロップしてインポート
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
      {dragover && (
        <div
          className="absolute inset-0 z-10"
          onDragOver={handleDragover}
          onDragLeave={() => {
            setDragEvent()
          }}
          onDrop={(e) => {
            setDragEvent()
            e.stopPropagation()
            e.preventDefault()
            onDrop?.(e, position)
          }}
        ></div>
      )}
    </div>
  )
}

const DndContext = createContext<{
  dragover: boolean
  setDragEvent: (e?: DragEvent) => void
}>({ dragover: false, setDragEvent: () => {} })
const DndProvider: React.FC<PropsWithChildren> = ({ children }) => {
  const [dragover, setDragover] = useState(false)

  const setDragEvent = useCallback((e?: DragEvent) => {
    setDragover(accept(e))
  }, [])

  return (
    <DndContext.Provider value={{ dragover, setDragEvent }}>
      {children}
    </DndContext.Provider>
  )
}

export function useDndContext() {
  return useContext(DndContext)
}
