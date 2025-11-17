import React, { useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { 
  Upload, 
  Download, 
  FileSpreadsheet, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  AlertCircle,
  FileText
} from 'lucide-react';
import api from '../utils/api';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';

export const BulkUploadPage = () => {
  const { user } = useAuth();
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadTask, setUploadTask] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(null);

  // Check if user is super admin
  if (user?.role !== 'super_admin') {
    return (
      <div className="space-y-6 fade-in">
        <Card className="glass-card">
          <CardContent className="p-12 text-center">
            <AlertCircle className="w-16 h-16 text-orange-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Access Denied</h3>
            <p className="text-gray-600">Only super administrators can access bulk upload functionality.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      const fileType = file.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx', 'xls'].includes(fileType)) {
        setSelectedFile(file);
        toast.success(`File selected: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please select CSV, XLSX, or XLS file.');
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    
    const file = e.dataTransfer.files[0];
    if (file) {
      const fileType = file.name.split('.').pop().toLowerCase();
      if (['csv', 'xlsx', 'xls'].includes(fileType)) {
        setSelectedFile(file);
        toast.success(`File selected: ${file.name}`);
      } else {
        toast.error('Invalid file type. Please select CSV, XLSX, or XLS file.');
      }
    }
  };

  const downloadTemplate = async (templateType) => {
    try {
      const response = await api.get(`/bulk-upload/templates/${templateType}`, {
        responseType: 'blob'
      });
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${templateType}_template.csv`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Template downloaded: ${templateType}_template.csv`);
    } catch (error) {
      toast.error('Failed to download template');
      console.error(error);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a file to upload');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      
      // Basic field mapping (can be enhanced with a UI wizard)
      const fieldMapping = {
        type: 'auto-detect' // Backend will auto-detect based on file structure
      };
      formData.append('field_mapping', JSON.stringify(fieldMapping));
      formData.append('validations', JSON.stringify({}));

      const response = await api.post('/bulk-upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setUploadTask(response.data.task_id);
      toast.success('Upload started! Monitoring progress...');
      
      // Poll for status
      pollUploadStatus(response.data.task_id);
      
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
      console.error(error);
      setUploading(false);
    }
  };

  const pollUploadStatus = async (taskId) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/bulk-upload/${taskId}`);
        const status = response.data;
        
        setUploadProgress(status);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          setUploading(false);
          toast.success('Upload completed successfully!');
          setSelectedFile(null);
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          setUploading(false);
          toast.error(`Upload failed: ${status.error}`);
        }
      } catch (error) {
        clearInterval(pollInterval);
        setUploading(false);
        toast.error('Failed to check upload status');
      }
    }, 2000); // Poll every 2 seconds
  };

  return (
    <div className="space-y-6 fade-in" data-testid="bulk-upload-page">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Bulk Upload</h1>
        <p className="text-gray-600 mt-1">Upload profiles and companies in bulk using CSV or Excel files</p>
      </div>

      {/* Download Templates */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Download className="w-5 h-5 mr-2" />
            Download Templates
          </CardTitle>
          <CardDescription>
            Download CSV templates to ensure your data is formatted correctly
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-2 border-gray-200 hover:border-blue-500 transition-colors cursor-pointer">
              <CardContent className="p-6">
                <FileSpreadsheet className="w-12 h-12 text-blue-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Profiles Template</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Template for uploading profile data with fields like name, job title, company, etc.
                </p>
                <Button 
                  onClick={() => downloadTemplate('profiles')} 
                  variant="outline" 
                  className="w-full"
                  data-testid="download-profiles-template"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </CardContent>
            </Card>

            <Card className="border-2 border-gray-200 hover:border-green-500 transition-colors cursor-pointer">
              <CardContent className="p-6">
                <FileSpreadsheet className="w-12 h-12 text-green-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Companies Template</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Template for uploading company data with fields like name, industry, size, etc.
                </p>
                <Button 
                  onClick={() => downloadTemplate('companies')} 
                  variant="outline" 
                  className="w-full"
                  data-testid="download-companies-template"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </CardContent>
            </Card>

            <Card className="border-2 border-gray-200 hover:border-purple-500 transition-colors cursor-pointer">
              <CardContent className="p-6">
                <FileSpreadsheet className="w-12 h-12 text-purple-600 mb-3" />
                <h3 className="font-semibold text-gray-900 mb-2">Combined Template</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Template for uploading both profiles and companies in a single file.
                </p>
                <Button 
                  onClick={() => downloadTemplate('combined')} 
                  variant="outline" 
                  className="w-full"
                  data-testid="download-combined-template"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Upload Section */}
      <Card className="glass-card">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Upload className="w-5 h-5 mr-2" />
            Upload File
          </CardTitle>
          <CardDescription>
            Drag and drop your CSV or Excel file, or click to browse
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              selectedFile ? 'border-green-500 bg-green-50' : 'border-gray-300 hover:border-blue-500 bg-gray-50'
            }`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            data-testid="upload-dropzone"
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="hidden"
              data-testid="file-input"
            />
            
            {selectedFile ? (
              <div className="space-y-3">
                <CheckCircle2 className="w-16 h-16 text-green-600 mx-auto" />
                <div>
                  <p className="text-lg font-semibold text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-600">
                    {(selectedFile.size / 1024).toFixed(2)} KB
                  </p>
                </div>
                <Badge variant="success" className="bg-green-100 text-green-800">
                  File Ready
                </Badge>
              </div>
            ) : (
              <div className="space-y-3">
                <Upload className="w-16 h-16 text-gray-400 mx-auto" />
                <div>
                  <p className="text-lg font-semibold text-gray-900">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-sm text-gray-600">
                    Supports CSV, XLSX, and XLS files
                  </p>
                </div>
              </div>
            )}
          </div>

          {selectedFile && (
            <div className="flex gap-3 mt-6">
              <Button
                onClick={handleUpload}
                disabled={uploading}
                className="btn-primary flex-1"
                data-testid="upload-button"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4 mr-2" />
                    Start Upload
                  </>
                )}
              </Button>
              
              <Button
                onClick={() => {
                  setSelectedFile(null);
                  setUploadProgress(null);
                }}
                variant="outline"
                disabled={uploading}
                data-testid="clear-button"
              >
                Clear
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Upload Progress */}
      {uploadProgress && (
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="flex items-center">
              {uploadProgress.status === 'completed' ? (
                <>
                  <CheckCircle2 className="w-5 h-5 mr-2 text-green-600" />
                  Upload Completed
                </>
              ) : uploadProgress.status === 'failed' ? (
                <>
                  <XCircle className="w-5 h-5 mr-2 text-red-600" />
                  Upload Failed
                </>
              ) : (
                <>
                  <Loader2 className="w-5 h-5 mr-2 animate-spin text-blue-600" />
                  Processing Upload
                </>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {uploadProgress.status === 'completed' && uploadProgress.result && (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Profiles Created</p>
                    <p className="text-2xl font-bold text-green-600">
                      {uploadProgress.result.profiles_created || 0}
                    </p>
                  </div>
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600">Companies Created</p>
                    <p className="text-2xl font-bold text-blue-600">
                      {uploadProgress.result.companies_created || 0}
                    </p>
                  </div>
                </div>
                {uploadProgress.result.errors && uploadProgress.result.errors.length > 0 && (
                  <div className="bg-orange-50 p-4 rounded-lg">
                    <p className="text-sm font-semibold text-orange-800 mb-2">
                      Warnings ({uploadProgress.result.errors.length})
                    </p>
                    <ul className="text-sm text-orange-700 space-y-1">
                      {uploadProgress.result.errors.slice(0, 5).map((error, idx) => (
                        <li key={idx}>• {error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
            
            {uploadProgress.status === 'failed' && (
              <div className="bg-red-50 p-4 rounded-lg">
                <p className="text-sm font-semibold text-red-800 mb-2">Error Details</p>
                <p className="text-sm text-red-700">{uploadProgress.error}</p>
              </div>
            )}
            
            {uploadProgress.status === 'processing' && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Processing...</span>
                  <Badge variant="secondary">In Progress</Badge>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Instructions */}
      <Card className="glass-card border-blue-200 bg-blue-50">
        <CardHeader>
          <CardTitle className="flex items-center text-blue-900">
            <FileText className="w-5 h-5 mr-2" />
            Upload Instructions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-blue-800">
            <li className="flex items-start">
              <span className="font-semibold mr-2">1.</span>
              <span>Download the appropriate template (Profiles, Companies, or Combined)</span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">2.</span>
              <span>Fill in your data following the template format exactly</span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">3.</span>
              <span>For combined uploads, use "profile" or "company" in the type column</span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">4.</span>
              <span>Upload your file - the system will automatically process it</span>
            </li>
            <li className="flex items-start">
              <span className="font-semibold mr-2">5.</span>
              <span>Monitor the progress and review results after completion</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
};
