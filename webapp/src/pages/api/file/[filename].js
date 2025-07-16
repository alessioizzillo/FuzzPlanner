import { readFile } from 'fs/promises'
import path from 'node:path'

//
const FILES = {
  executable_files: 'static',
  data_channels: 'run',
  interactions: 'run',
  processes: 'run'
}

//
const DIR_ROOT = path.join('/', 'FuzzPlanner', 'runtime_tmp', 'analysis', 'results')

function getStaticDir (brandId, fwId) { 
  return path.join(DIR_ROOT, brandId, fwId, 'static_analysis', 'data') 
}

function getRunDir (brandId, fwId, runId) { 
  return path.join(DIR_ROOT, brandId, fwId, 'dynamic_analysis', runId, 'data') 
}

//
async function getFile (dir, name) {
  try {
    return await readFile(path.join(dir, `${name}.json`), 'utf-8')
  } catch (e) {
    if (e.code === 'ENOENT' && e.syscall === 'open') {
      return null
    }
    console.log('getFile', dir, name)
    console.log(e)
  }
}
async function getStaticFile (name, brandId, fwId) {
  const dir = getStaticDir(brandId, fwId)
  return await getFile(dir, name)
}
async function getRunFile (name, brandId, fwId, runId) {
  const dir = getRunDir(brandId, fwId, runId)
  return await getFile(dir, name)
}

async function handleGet (req, res) {
  const { filename, brandId, fwId, runId } = req.query
  const fileType = FILES[filename]
  if (!fileType || !(fileType === 'static' || fileType === 'run')) {
    res.status(400).send({ message: 'Filename/filetype invalid' })
  } else {
    try {
      let data = null
      if (fileType === 'static') {
        data = await getStaticFile(filename, brandId, fwId)
      } else if (fileType === 'run') {
        data = await getRunFile(filename, brandId, fwId, runId)
      }
      if (data === null) {
        res.status(400).send({ message: 'File not found' })
      } else {
        res.status(200).json(JSON.parse(data))
      }
    } catch (_e) {
      res.status(400).send({ message: 'File not found' })
    }
  }
}

export default async function handler (req, res) {
  await handleGet(req, res)
}

