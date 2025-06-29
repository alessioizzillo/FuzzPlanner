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
function getStaticDir (fwId) { return path.join(DIR_ROOT, fwId, 'static_analysis', 'data') }
function getRunDir (fwId, runId) { return path.join(DIR_ROOT, fwId, 'dynamic_analysis', runId, 'data') }

//
async function getFile (dir, name) {
  try {
    return await readFile(path.join(dir, `${name}.json`), 'utf-8')
  } catch (e) {
    console.log('getFile', dir, name)
    console.log(e)
  }
}
async function getStaticFile (name, fwId) {
  const dir = getStaticDir(fwId)
  return await getFile(dir, name)
}
async function getRunFile (name, fwId, runId) {
  const dir = getRunDir(fwId, runId)
  return await getFile(dir, name)
}

async function handleGet (req, res) {
  const { filename, fwId, runId } = req.query
  const fileType = FILES[filename]
  if (!fileType || !(fileType === 'static' || fileType === 'run')) {
    res.status(400).send({ message: 'Filename/filetype invalid' })
  } else {
    try {
      let data = {}
      if (fileType === 'static') {
        data = await getStaticFile(filename, fwId)
      } else if (fileType === 'run') {
        data = await getRunFile(filename, fwId, runId)
      }
      res.status(200).json(JSON.parse(data))
    } catch (_e) {
      res.status(400).send({ message: 'File not found' })
    }
  }
}

export default async function handler (req, res) {
  await handleGet(req, res)
}
