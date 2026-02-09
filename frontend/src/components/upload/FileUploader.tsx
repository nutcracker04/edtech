import { useCallback, useState } from 'react';
import { Upload, FileImage, X, Loader2, CheckCircle2 } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';

interface FileUploaderProps {
  onFileSelect: (file: File) => void;
  loading?: boolean;
  progress?: number;
  status?: 'idle' | 'uploading' | 'processing' | 'completed' | 'error';
  error?: string;
  accept?: string;
  maxSize?: number; // in MB
  label?: string;
}

export function FileUploader({
  onFileSelect,
  loading = false,
  progress = 0,
  status = 'idle',
  error,
  accept = 'image/*',
  maxSize = 10,
  label = 'Upload Test Paper',
}: FileUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const validateFile = (file: File): string | null => {
    // Check file type
    // Check file type - simple validation based on accept prop
    if (accept === 'image/*' && !file.type.startsWith('image/')) {
      return 'Please upload an image file';
    }

    // If accept allows specific types, we should ideally check against them
    // For now, if it's PDF and we allow it, explicitly check
    if (file.type === 'application/pdf') {
      if (!accept?.includes('application/pdf') && !accept?.includes('.pdf')) {
        return 'PDF files are not allowed';
      }
    } else if (!file.type.startsWith('image/') && accept?.startsWith('image/')) {
      return 'Please upload an image file';
    }

    // Check file size
    const sizeMB = file.size / (1024 * 1024);
    if (sizeMB > maxSize) {
      return `File size must be less than ${maxSize}MB`;
    }

    return null;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      const error = validateFile(file);

      if (error) {
        // Show error (you might want to use a toast here)
        console.error(error);
        return;
      }

      setSelectedFile(file);
      onFileSelect(file);
    }
  }, [onFileSelect, maxSize]);

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const error = validateFile(file);

      if (error) {
        console.error(error);
        return;
      }

      setSelectedFile(file);
      onFileSelect(file);
    }
  }, [onFileSelect, maxSize]);

  const handleClear = () => {
    setSelectedFile(null);
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'uploading':
      case 'processing':
        return <Loader2 className="h-8 w-8 animate-spin text-primary" />;
      case 'completed':
        return <CheckCircle2 className="h-8 w-8 text-green-500" />;
      case 'error':
        return <X className="h-8 w-8 text-red-500" />;
      default:
        return <FileImage className="h-8 w-8 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'uploading':
        return 'Uploading...';
      case 'processing':
        return 'Processing with OCR...';
      case 'completed':
        return 'Processing complete!';
      case 'error':
        return error || 'Upload failed';
      default:
        return 'No file selected';
    }
  };

  return (
    <Card
      className={cn(
        'relative border-2 border-dashed transition-colors',
        dragActive && 'border-primary bg-primary/5',
        error && 'border-destructive',
        loading && 'pointer-events-none opacity-60'
      )}
      onDragEnter={handleDrag}
      onDragLeave={handleDrag}
      onDragOver={handleDrag}
      onDrop={handleDrop}
    >
      <div className="p-8">
        {/* Upload Area */}
        {!selectedFile ? (
          <div className="flex flex-col items-center justify-center space-y-4 text-center">
            <Upload className="h-12 w-12 text-muted-foreground" />
            <div>
              <p className="text-lg font-medium">{label}</p>
              <p className="text-sm text-muted-foreground mt-1">
                Drag and drop or click to browse
              </p>
              <p className="text-xs text-muted-foreground mt-2">
                Supports: JPG, PNG, PDF • Max size: {maxSize}MB
              </p>
            </div>
            <Button variant="outline" onClick={() => document.getElementById('file-upload')?.click()}>
              Browse Files
            </Button>
            <input
              id="file-upload"
              type="file"
              className="hidden"
              accept={accept}
              onChange={handleChange}
              disabled={loading}
            />
          </div>
        ) : (
          <div className="space-y-4">
            {/* File Preview */}
            <div className="flex items-start gap-4">
              <div className="flex-shrink-0">
                {getStatusIcon()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {getStatusText()}
                </p>
              </div>
              {status === 'idle' && (
                <Button variant="ghost" size="icon" onClick={handleClear}>
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Progress Bar */}
            {(status === 'uploading' || status === 'processing') && (
              <div className="space-y-2">
                <Progress value={progress} />
                <p className="text-xs text-muted-foreground text-center">
                  {progress}% complete
                </p>
              </div>
            )}

            {/* Error Message */}
            {error && status === 'error' && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
