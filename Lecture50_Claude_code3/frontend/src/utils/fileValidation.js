import {
  ALLOWED_EXTENSIONS,
  MAX_FILE_SIZE_BYTES,
  MAX_FILE_SIZE_MB,
} from '../config/constants'
import { formatBytes } from './formatters'

// Pure functions: take files, return an error message or null.
// No React here, so these are easy to test and reuse.

export function validateFileList(fileList) {
  if (!fileList || fileList.length === 0) return 'No file selected.'
  if (fileList.length > 1) return 'Please upload only one file at a time.'
  return validateFile(fileList[0])
}

export function validateFile(file) {
  const name = file.name.toLowerCase()
  const hasAllowedExtension = ALLOWED_EXTENSIONS.some((ext) => name.endsWith(ext))

  if (!hasAllowedExtension) {
    return `"${file.name}" isn't supported. Upload a .csv or .xlsx file.`
  }
  if (file.size === 0) {
    return `"${file.name}" is empty.`
  }
  if (file.size > MAX_FILE_SIZE_BYTES) {
    return `"${file.name}" is ${formatBytes(file.size)}. The limit is ${MAX_FILE_SIZE_MB} MB.`
  }
  return null
}
