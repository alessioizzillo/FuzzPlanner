import path from 'node:path'

import { getDirectories } from '@/apiUtils'

const DIR_ROOT = path.join(process.cwd(), 'src', 'data')

async function handleGet (req, res) {
  try {
    const data = await getDirectories(DIR_ROOT)
    res.status(200).json(data)
  } catch (e) {
    console.log(e)
    res.status(400).send({ message: 'GetDirRoot Error' })
  }
}

export default async function handler (req, res) {
  await handleGet(req, res)
}
