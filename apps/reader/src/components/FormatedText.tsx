import React from 'react'

function cleanUpText(str: string, strict = false): string {
  str = str.replace(/^\s+|\s+$/g, '')

  if (strict) {
    str = str.replace(/\n{2,}/g, '\n')
  }

  return str
}

export const FormattedText = ({
  text,
  strict = false,
  className,
}: {
  text: string
  strict?: boolean
  className?: string
}) => (
  <p className={className}>
    {cleanUpText(text, strict)
      .split('\n')
      .map((line, index) => (
        <React.Fragment key={index}>
          {line}
          <br />
        </React.Fragment>
      ))}
  </p>
)
