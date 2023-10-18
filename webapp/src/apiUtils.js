import { readdir } from 'fs/promises'

export async function getDirectories (source) {
  return (await readdir(source, { withFileTypes: true }))
    .filter(dirent => dirent.isDirectory())
    .map(dirent => dirent.name)
}
