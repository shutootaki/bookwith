import JSZip from 'jszip'

import { BookRecord, db } from './db'
import { BookDetail } from './hooks'

interface SerializedBooks {
  version: number
  books: BookDetail[]
}

export const DATA_FILENAME = 'data.json'

function deserializeData(text: string) {
  const { books } = JSON.parse(text) as SerializedBooks

  return books
}

export async function unpack(file: File) {
  const zip = new JSZip()
  await zip.loadAsync(file)

  const booksJSON = zip.file(DATA_FILENAME)
  const coversJSON = zip.file('covers.json')
  if (!booksJSON || !coversJSON) return

  const books = deserializeData(await booksJSON.async('text'))

  // 型の問題を回避するために型アサーションを使用
  db?.books.bulkPut(books as unknown as BookRecord[])

  const coversText = await coversJSON.async('text')
  db?.covers.bulkPut(JSON.parse(coversText))

  const folder = zip.folder('files')
  folder?.forEach(async (_, f) => {
    const book = books.find((b) => `files/${b.name}` === f.name)
    if (!book) return

    const data = await f.async('blob')
    const file = new File([data], book.name)
    db?.files.put({ file, id: book.id })
  })
}
