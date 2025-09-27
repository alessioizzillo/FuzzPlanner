import {
  TrashIcon,
  DocumentTextIcon,
  PencilSquareIcon,
  ChartBarIcon,
  ClockIcon,
  XMarkIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  PaperAirplaneIcon,
  RocketLaunchIcon,
  MagnifyingGlassIcon,
  BoltIcon,
  SparklesIcon
} from '@heroicons/react/24/outline'

const iconMap = {
  // Actions
  'delete': TrashIcon,
  'remove': TrashIcon,
  'trash': TrashIcon,
  'close': XMarkIcon,
  'cancel': XMarkIcon,
  'play': PlayIcon,
  'pause': PauseIcon,
  'stop': StopIcon,
  'loading': ArrowPathIcon,
  'refresh': ArrowPathIcon,
  'send': PaperAirplaneIcon,
  'launch': RocketLaunchIcon,

  // Content
  'document': DocumentTextIcon,
  'details': DocumentTextIcon,
  'metadata': PencilSquareIcon,
  'stats': ChartBarIcon,
  'chart': ChartBarIcon,

  // Status
  'success': CheckCircleIcon,
  'warning': ExclamationTriangleIcon,
  'error': XMarkIcon,
  'info': InformationCircleIcon,
  'clock': ClockIcon,
  'time': ClockIcon,

  // Features
  'search': MagnifyingGlassIcon,
  'analyze': MagnifyingGlassIcon,
  'target': SparklesIcon,
  'power': BoltIcon,
  'rocket': RocketLaunchIcon
}

export default function Icon({
  name,
  className = "w-5 h-5",
  solid = false,
  ...props
}) {
  // Import solid versions if needed
  const solidIconMap = solid ? {
    'delete': require('@heroicons/react/24/solid').TrashIcon,
    'remove': require('@heroicons/react/24/solid').TrashIcon,
    'trash': require('@heroicons/react/24/solid').TrashIcon,
    'close': require('@heroicons/react/24/solid').XMarkIcon,
    'cancel': require('@heroicons/react/24/solid').XMarkIcon,
    'play': require('@heroicons/react/24/solid').PlayIcon,
    'pause': require('@heroicons/react/24/solid').PauseIcon,
    'stop': require('@heroicons/react/24/solid').StopIcon,
    'loading': require('@heroicons/react/24/solid').ArrowPathIcon,
    'refresh': require('@heroicons/react/24/solid').ArrowPathIcon,
    'send': require('@heroicons/react/24/solid').PaperAirplaneIcon,
    'launch': require('@heroicons/react/24/solid').RocketLaunchIcon,
    'document': require('@heroicons/react/24/solid').DocumentTextIcon,
    'details': require('@heroicons/react/24/solid').DocumentTextIcon,
    'metadata': require('@heroicons/react/24/solid').PencilSquareIcon,
    'stats': require('@heroicons/react/24/solid').ChartBarIcon,
    'chart': require('@heroicons/react/24/solid').ChartBarIcon,
    'success': require('@heroicons/react/24/solid').CheckCircleIcon,
    'warning': require('@heroicons/react/24/solid').ExclamationTriangleIcon,
    'error': require('@heroicons/react/24/solid').XMarkIcon,
    'info': require('@heroicons/react/24/solid').InformationCircleIcon,
    'clock': require('@heroicons/react/24/solid').ClockIcon,
    'time': require('@heroicons/react/24/solid').ClockIcon,
    'search': require('@heroicons/react/24/solid').MagnifyingGlassIcon,
    'analyze': require('@heroicons/react/24/solid').MagnifyingGlassIcon,
    'target': require('@heroicons/react/24/solid').SparklesIcon,
    'power': require('@heroicons/react/24/solid').BoltIcon,
    'rocket': require('@heroicons/react/24/solid').RocketLaunchIcon
  } : iconMap

  const IconComponent = (solid ? solidIconMap[name] : iconMap[name]) || DocumentTextIcon

  return (
    <IconComponent
      className={className}
      {...props}
    />
  )
}

// Export individual icons for direct use if needed
export {
  TrashIcon,
  DocumentTextIcon,
  PencilSquareIcon,
  ChartBarIcon,
  ClockIcon,
  XMarkIcon,
  PlayIcon,
  PauseIcon,
  StopIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  PaperAirplaneIcon,
  RocketLaunchIcon,
  MagnifyingGlassIcon,
  BoltIcon,
  SparklesIcon
}