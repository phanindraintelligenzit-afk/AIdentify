import React from 'react'
import { useAuth } from '../contexts/AuthContext'
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Badge } from '../components/ui/Badge'
import { Alert } from '../components/ui/Alert'
import { User, Key, Shield, Mail, Bell, LogOut, Save, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { api } from '../services/api'

const profileSchema = z.object({
  full_name: z.string().min(1, 'Name is required').optional(),
  email: z.string().email('Invalid email').optional(),
})

const passwordSchema = z.object({
  current_password: z.string().min(1, 'Current password is required'),
  new_password: z.string().min(8, 'Password must be at least 8 characters'),
  confirm_password: z.string(),
}).refine((data) => data.new_password === data.confirm_password, {
  message: 'Passwords do not match',
  path: ['confirm_password'],
})

type ProfileForm = z.infer<typeof profileSchema>
type PasswordForm = z.infer<typeof passwordSchema>

export const Settings = () => {
  const { user, logout, refreshUser } = useAuth()
  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'api' | 'danger'>('profile')
  const [profileMessage, setProfileMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  
  const profileForm = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: user?.full_name || '',
      email: user?.email || '',
    },
  })
  
  const passwordForm = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  })
  
  const [profileSaving, setProfileSaving] = useState(false)
  const [passwordSaving, setPasswordSaving] = useState(false)
  
  const onProfileSubmit = async (data: ProfileForm) => {
    setProfileSaving(true)
    setProfileMessage(null)
    try {
      await api.put('/auth/me', data)
      await refreshUser()
      setProfileMessage({ type: 'success', text: 'Profile updated successfully' })
    } catch (err: any) {
      setProfileMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile' })
    } finally {
      setProfileSaving(false)
    }
  }
  
  const onPasswordSubmit = async (data: PasswordForm) => {
    setPasswordSaving(true)
    setProfileMessage(null)
    try {
      await api.post('/auth/change-password', {
        current_password: data.current_password,
        new_password: data.new_password,
      })
      passwordForm.reset()
      setProfileMessage({ type: 'success', text: 'Password changed successfully' })
    } catch (err: any) {
      setProfileMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to change password' })
    } finally {
      setPasswordSaving(false)
    }
  }
  
  const handleLogout = () => {
    logout()
  }
  
  const handleDeleteAccount = () => {
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      if (window.confirm('This will permanently delete all your contracts, playbooks, and data. Type "DELETE" to confirm.')) {
        // Would call delete account API
        alert('Account deletion would be implemented here')
      }
    }
  }
  
  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'password', label: 'Password', icon: Key },
    { id: 'api', label: 'API Keys', icon: Shield },
    { id: 'danger', label: 'Danger Zone', icon: AlertCircle },
  ]
  
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Settings</h1>
        <p className="text-muted-foreground mt-1">Manage your account settings and preferences</p>
      </div>
      
      {profileMessage && (
        <Alert variant={profileMessage.type === 'success' ? 'success' : 'destructive'} className="mb-4">
          {profileMessage.text}
        </Alert>
      )}
      
      {/* Tab Navigation */}
      <div className="flex gap-1 bg-muted p-1 rounded-lg">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Profile Tab */}
      {activeTab === 'profile' && (
        <Card>
          <CardHeader>
            <CardTitle>Profile Information</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={profileForm.handleSubmit(onProfileSubmit)} className="space-y-4">
              <Input
                label="Full Name"
                placeholder="John Doe"
                {...profileForm.register('full_name')}
                disabled={profileSaving}
              />
              <Input
                label="Email"
                type="email"
                placeholder="you@company.com"
                {...profileForm.register('email')}
                disabled={profileSaving}
              />
              <Button type="submit" loading={profileSaving}>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
      
      {/* Password Tab */}
      {activeTab === 'password' && (
        <Card>
          <CardHeader>
            <CardTitle>Change Password</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={passwordForm.handleSubmit(onPasswordSubmit)} className="space-y-4">
              <Input
                label="Current Password"
                type="password"
                {...passwordForm.register('current_password')}
                disabled={passwordSaving}
              />
              <Input
                label="New Password"
                type="password"
                {...passwordForm.register('new_password')}
                disabled={passwordSaving}
              />
              <Input
                label="Confirm New Password"
                type="password"
                {...passwordForm.register('confirm_password')}
                disabled={passwordSaving}
              />
              <Button type="submit" loading={passwordSaving}>
                <Key className="mr-2 h-4 w-4" />
                Change Password
              </Button>
            </form>
          </CardContent>
        </Card>
      )}
      
      {/* API Keys Tab */}
      {activeTab === 'api' && (
        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">API Access Token</p>
                    <p className="text-sm text-muted-foreground">Use this token for API authentication</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Regenerate
                  </Button>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <code className="flex-1 bg-background px-3 py-2 rounded text-sm font-mono text-muted-foreground">
                    cra_live_••••••••••••••••••••••••••••••••
                  </code>
                  <Button variant="ghost" size="sm">
                    Copy
                  </Button>
                </div>
              </div>
              <p className="text-sm text-muted-foreground">
                Keep your API keys secure. They provide access to your contracts and playbooks.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Danger Zone Tab */}
      {activeTab === 'danger' && (
        <Card className="border-destructive/20">
          <CardHeader>
            <CardTitle className="text-destructive flex items-center gap-2">
              <AlertCircle className="h-5 w-5" />
              Danger Zone
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Delete Account</p>
                  <p className="text-sm text-muted-foreground">Permanently delete your account and all associated data</p>
                </div>
                <Button variant="destructive" onClick={handleDeleteAccount}>
                  <Trash2 className="mr-2 h-4 w-4" />
                  Delete Account
                </Button>
              </div>
            </div>
            
            <div className="p-4 bg-muted rounded-lg border border-border">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium">Logout</p>
                  <p className="text-sm text-muted-foreground">Sign out of your account</p>
                </div>
                <Button variant="outline" onClick={handleLogout}>
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Need AlertCircle import
import { AlertCircle, Trash2 } from 'lucide-react'