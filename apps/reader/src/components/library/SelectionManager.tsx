import { Trash2, X } from 'lucide-react'
import React from 'react'
import { toast } from 'sonner'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@flow/reader/components/ui/alert-dialog'

import { Button } from '../'
import { useTranslation } from '../../hooks'
import { deleteBooksFromAPI } from '../../lib/apiHandler/bookApiHandler'

interface SelectionManagerProps {
  select: boolean
  selectedBookIds: Set<string>
  allSelected: boolean
  onToggleSelect: () => void
  onSelectAll: () => void
  onDeselectAll: () => void
  onImportComplete: () => void
  hasBooks: boolean
}

export const SelectionManager: React.FC<SelectionManagerProps> = ({
  select,
  selectedBookIds,
  allSelected,
  onToggleSelect,
  onSelectAll,
  onDeselectAll,
  onImportComplete,
  hasBooks,
}) => {
  const t = useTranslation('home')

  if (!hasBooks && !select) {
    return null
  }

  return (
    <>
      {select && (
        <div className="bg-secondary mb-2 flex items-center justify-between rounded-lg px-3">
          <span className="text-secondary-foreground text-sm">
            {t('selected_books', { count: selectedBookIds.size })}
          </span>
          <Button variant="ghost" size="sm" onClick={onToggleSelect}>
            <X className="h-4 w-4" />
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {hasBooks && (
            <Button variant="outline" size="sm" onClick={onToggleSelect}>
              {t(select ? 'cancel' : 'select')}
            </Button>
          )}
          {select && (
            <Button
              variant="outline"
              size="sm"
              onClick={allSelected ? onDeselectAll : onSelectAll}
            >
              {t(allSelected ? 'deselect_all' : 'select_all')}
            </Button>
          )}
        </div>
        {select && (
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="destructive"
                size="sm"
                disabled={selectedBookIds.size === 0}
                className="ml-auto"
              >
                <Trash2 className="h-4 w-4" />
                {t('delete')} ({selectedBookIds.size})
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>{t('delete_confirmation')}</AlertDialogTitle>
                <AlertDialogDescription>
                  {t('delete_confirmation_message')}
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>{t('cancel')}</AlertDialogCancel>
                <AlertDialogAction
                  onClick={async () => {
                    onToggleSelect()
                    await deleteBooksFromAPI([...selectedBookIds])
                    onImportComplete()
                    toast.success(t('delete_success'))
                  }}
                >
                  {t('delete')}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>
    </>
  )
}
