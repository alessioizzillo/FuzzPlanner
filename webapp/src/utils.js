import axios from 'axios'

export function handleHttpError (error) {
  if (error.response) {
    console.log('Error response')
    const res = error.response
    console.log(res.status)
    console.log(res.data)
    console.log(res.headers)
  } else if (error.request) {
    console.log('Error request')
    console.log(error.request)
  } else {
    console.log('Error')
    console.log(error.message)
  }
}

export async function getHttp (url, headers = {}, params = {}) {
  try {
    const { data } = await axios.get(url, { params, headers })
    return data
  } catch (e) {
    handleHttpError(e)
  }
}

export function makeId (length) {
  let result = ''
  const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const charactersLength = characters.length
  let counter = 0
  while (counter < length) {
    result += characters.charAt(Math.floor(Math.random() * charactersLength))
    counter += 1
  }
  return result
}

export function sanitizeId (str) {
  // Remove any leading or trailing whitespace
  str = str.trim()
  // Replace any characters that are not alphanumeric, underscore, or hyphen with an underscore
  str = str.replace(/[^a-zA-Z0-9_-]/g, '_')
  // Ensure the first character is a letter (IDs cannot start with a number)
  if (/^[^a-zA-Z]/.test(str)) {
    str = 'id_' + str // Prepend 'id_' if the first character is not a letter
  }
  return str
}
