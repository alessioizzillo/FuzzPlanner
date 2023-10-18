import path from 'node:path'

import { getDirectories } from '@/apiUtils'

const DIR_ROOT = path.join(process.cwd(), 'src', 'data')

async function handleGet (req, res) {
  const { fwId } = req.query
  try {
    const dirFw = path.join(DIR_ROOT, fwId, 'dynamic_analysis')
    const data = await getDirectories(dirFw)
    res.status(200).json(data)
  } catch (e) {
    console.log(e)
    res.status(400).send({ message: 'GetDirFw Error' })
  }
}

export default async function handler (req, res) {
  await handleGet(req, res)
}
