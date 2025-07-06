import React from 'react'

import { useTranslation } from '../../hooks'
import { lock } from '../../utils/styles'
import { Book } from '../Book'

interface BookGridProps {
  books: any[]
  covers: any
  select: boolean
  loading?: string
  onToggleBook: (bookId: string) => void
  hasBook: (bookId: string) => boolean
  isCoverLoading: boolean
}

export const BookGrid: React.FC<BookGridProps> = ({
  books,
  covers,
  select,
  loading,
  onToggleBook,
  hasBook,
  isCoverLoading,
}) => {
  const t = useTranslation('home')

  if (books.length === 0) {
    return (
      <div className="flex h-full items-center justify-center">
        <p className="text-muted-foreground">{t('no_books_message')}</p>
      </div>
    )
  }

  return (
    <div className="scroll h-full">
      <ul
        className="grid"
        style={{
          gridTemplateColumns: `repeat(auto-fill, minmax(calc(80px + 3vw), 1fr))`,
          columnGap: lock(16, 32),
          rowGap: lock(24, 40),
        }}
      >
        {books.map((book) => (
          <Book
            key={book.id}
            book={book as any}
            covers={covers}
            select={select}
            selected={hasBook(book.id)}
            loading={loading === book.id}
            toggle={onToggleBook}
            isLoading={isCoverLoading}
          />
        ))}
      </ul>
    </div>
  )
}
