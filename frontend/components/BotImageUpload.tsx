'use client'

import React, { useState, useRef, useCallback } from 'react'
import { createClient } from '@/lib/supabase'
import { Upload, X, Loader2 } from 'lucide-react'

interface BotImageUploadProps {
  configId: string
  currentImageUrl: string | null
  onUploadComplete: (url: string) => void
  className?: string
}

export function BotImageUpload({
  configId,
  currentImageUrl,
  onUploadComplete,
  className = ''
}: BotImageUploadProps) {
  const [uploading, setUploading] = useState(false)
  const [preview, setPreview] = useState<string | null>(currentImageUrl)
  const [error, setError] = useState<string | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Sync preview with currentImageUrl when it changes (e.g., from SSE update)
  React.useEffect(() => {
    setPreview(currentImageUrl)
  }, [currentImageUrl])

  // Resize image to 1024x1024
  const resizeImage = (file: File): Promise<Blob> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        const img = new Image()
        img.onload = () => {
          const canvas = document.createElement('canvas')
          const ctx = canvas.getContext('2d')

          if (!ctx) {
            reject(new Error('Could not get canvas context'))
            return
          }

          // Set canvas size to 1024x1024
          canvas.width = 1024
          canvas.height = 1024

          // Calculate crop dimensions to maintain aspect ratio
          const size = Math.min(img.width, img.height)
          const x = (img.width - size) / 2
          const y = (img.height - size) / 2

          // Draw cropped and resized image
          ctx.drawImage(img, x, y, size, size, 0, 0, 1024, 1024)

          // Convert to blob
          canvas.toBlob((blob) => {
            if (blob) {
              resolve(blob)
            } else {
              reject(new Error('Could not create blob from canvas'))
            }
          }, 'image/jpeg', 0.9)
        }
        img.onerror = () => reject(new Error('Failed to load image'))
        img.src = e.target?.result as string
      }
      reader.onerror = () => reject(new Error('Failed to read file'))
      reader.readAsDataURL(file)
    })
  }

  const handleUpload = async (file: File) => {
    setError(null)

    // Validate file
    if (!file.type.startsWith('image/')) {
      setError('Please upload an image file (JPG, PNG, or WebP)')
      return
    }

    if (file.size > 5 * 1024 * 1024) { // 5MB limit
      setError('Image must be less than 5MB')
      return
    }

    setUploading(true)

    try {
      // Get Supabase client
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        setError('Not authenticated')
        return
      }

      // Resize image to 1024x1024
      const resizedBlob = await resizeImage(file)

      // Create preview
      const previewUrl = URL.createObjectURL(resizedBlob)
      setPreview(previewUrl)

      // Upload to Supabase Storage
      const fileName = `${configId}.jpg`
      const filePath = `${session.user.id}/${fileName}`

      const { error: uploadError } = await supabase.storage
        .from('bot-avatars')
        .upload(filePath, resizedBlob, {
          cacheControl: '3600',
          upsert: true, // Replace if exists
          contentType: 'image/jpeg'
        })

      if (uploadError) {
        throw uploadError
      }

      // Get public URL
      const { data: { publicUrl } } = supabase.storage
        .from('bot-avatars')
        .getPublicUrl(filePath)

      // Update configuration with new URL
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/v2/config/${configId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          profile_image_url: publicUrl
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update configuration')
      }

      // Notify parent component
      onUploadComplete(publicUrl)

    } catch (err) {
      console.error('Upload error:', err)
      setError(err instanceof Error ? err.message : 'Upload failed')
      setPreview(currentImageUrl) // Revert to current image
    } finally {
      setUploading(false)
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleUpload(file)
    }
  }

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleUpload(file)
    }
  }, [])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleRemove = async () => {
    if (!currentImageUrl) return

    setError(null)
    setUploading(true)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      if (!session) {
        setError('Not authenticated')
        return
      }

      // Update configuration to remove image URL
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/v2/config/${configId}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          profile_image_url: null
        })
      })

      if (!response.ok) {
        throw new Error('Failed to update configuration')
      }

      setPreview(null)
      onUploadComplete('')

    } catch (err) {
      console.error('Remove error:', err)
      setError(err instanceof Error ? err.message : 'Remove failed')
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className={`relative ${className}`}>
      {/* Image preview or placeholder */}
      <div
        className={`
          relative w-12 h-12 rounded-full border-2 border-brass overflow-hidden cursor-pointer
          ${isDragging ? 'border-brass/80 bg-brass/10' : 'border-brass/40'}
          ${uploading ? 'opacity-50 cursor-wait' : ''}
        `}
        onClick={() => !uploading && fileInputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
      >
        {preview ? (
          <img
            src={preview}
            alt="Bot avatar"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-bg-tertiary text-text-tertiary text-xs">
            <Upload className="h-4 w-4" />
          </div>
        )}

        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-bg-primary/80">
            <Loader2 className="h-4 w-4 animate-spin text-brass" />
          </div>
        )}

        {preview && !uploading && (
          <button
            onClick={(e) => {
              e.stopPropagation()
              handleRemove()
            }}
            className="absolute top-0 right-0 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity"
            title="Remove image"
          >
            <X className="h-3 w-3 text-white" />
          </button>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        onChange={handleFileSelect}
        className="hidden"
      />

      {/* Error message */}
      {error && (
        <div className="absolute top-full left-0 mt-1 text-xs text-red-400 whitespace-nowrap">
          {error}
        </div>
      )}
    </div>
  )
}
