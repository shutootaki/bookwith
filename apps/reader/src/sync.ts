import { saveAs } from 'file-saver'
import JSZip from 'jszip'

import { BookRecord, db } from './db'
import { BookDetail } from './hooks'

interface SerializedBooks {
  version: number
  books: BookDetail[]
}

const VERSION = 1
export const DATA_FILENAME = 'data.json'

function serializeData(books?: BookDetail[]) {
  return JSON.stringify({
    version: VERSION,
    books,
  })
}

function deserializeData(text: string) {
  const { version, books } = JSON.parse(text) as SerializedBooks

  return books
}

export async function pack() {
  const books = await db?.books.toArray()
  const covers = await db?.covers.toArray()
  const files = await db?.files.toArray()

  const zip = new JSZip()
  // 型の問題を回避するために型アサーションを使用
  zip.file(DATA_FILENAME, serializeData(books as unknown as BookDetail[]))
  zip.file('covers.json', JSON.stringify(covers))

  const folder = zip.folder('files')
  files?.forEach((f) => folder?.file(f.file.name, f.file))

  const date = new Intl.DateTimeFormat('fr-CA').format().replaceAll('-', '')

  return zip.generateAsync({ type: 'blob' }).then((content) => {
    saveAs(content, `flow_backup_${date}.zip`)
  })
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
