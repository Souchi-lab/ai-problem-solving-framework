import { useState } from 'react'
import type { ModalConfig } from '../types'

export function useModalState() {
  const [modalConfig, setModalConfig] = useState<ModalConfig | null>(null)
  const [viewerConfigModalOpen, setViewerConfigModalOpen] = useState(false)
  const [artifactModalOpen, setArtifactModalOpen] = useState(false)
  const [specialistModalOpen, setSpecialistModalOpen] = useState(false)
  const [createSpecialistModalOpen, setCreateSpecialistModalOpen] = useState(false)
  const [autoLoopLaunchModalOpen, setAutoLoopLaunchModalOpen] = useState(false)
  const [rallyModalOpen, setRallyModalOpen] = useState(false)
  const [judgeChatOpen, setJudgeChatOpen] = useState(false)

  return {
    modalConfig,
    setModalConfig,
    viewerConfigModalOpen,
    setViewerConfigModalOpen,
    artifactModalOpen,
    setArtifactModalOpen,
    specialistModalOpen,
    setSpecialistModalOpen,
    createSpecialistModalOpen,
    setCreateSpecialistModalOpen,
    autoLoopLaunchModalOpen,
    setAutoLoopLaunchModalOpen,
    rallyModalOpen,
    setRallyModalOpen,
    judgeChatOpen,
    setJudgeChatOpen,
  }
}
