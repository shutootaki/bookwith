import Head from 'next/head'
import { useRouter } from 'next/router'
import React, { useEffect, useState } from 'react'

import { ReaderGridView } from '../components'
import { Library } from '../components/Library'
import { useDisablePinchZooming } from '../hooks'
import { fetchBook, handleFiles } from '../lib/apiHandler/importHandlers'
import { reader, useReaderSnapshot } from '../models'

const SOURCE = 'src'

export default function Index() {
  const { focusedTab } = useReaderSnapshot()
  const router = useRouter()
  const src = new URL(window.location.href).searchParams.get(SOURCE)
  const [loading, setLoading] = useState(!!src)

  useDisablePinchZooming()

  useEffect(() => {
    let src = router.query[SOURCE]
    if (!src) return
    if (!Array.isArray(src)) src = [src]

    Promise.all(
      src.map((s) =>
        fetchBook(s).then((b) => {
          if (b) reader.addTab(b as any)
        }),
      ),
    ).finally(() => setLoading(false))
  }, [router.query])

  useEffect(() => {
    if ('launchQueue' in window && 'LaunchParams' in window) {
      window.launchQueue.setConsumer((params) => {
        if (params.files.length) {
          Promise.all(params.files.map((f) => f.getFile()))
            .then((files) => handleFiles(files))
            .then((result) => {
              if (result && 'newBooks' in result) {
                result.newBooks.forEach((b: any) => reader.addTab(b))
              }
            })
        }
      })
    }
  }, [])

  useEffect(() => {
    router.beforePopState(({ url }) => {
      if (url === '/') {
        reader.clear()
      }
      return true
    })
  }, [router])

  return (
    <>
      <Head>
        {/* https://github.com/microsoft/vscode/blob/36fdf6b697cba431beb6e391b5a8c5f3606975a1/src/vs/code/browser/workbench/workbench.html#L16 */}
        {/* Disable pinch zooming */}
        <meta
          name="viewport"
          content="width=device-width, initial-scale=1.0, maximum-scale=1.0, minimum-scale=1.0, user-scalable=no"
        />
        <title>{focusedTab?.title ?? 'Bookwith'}</title>
      </Head>
      <ReaderGridView />
      {loading || <Library />}
    </>
  )
}
