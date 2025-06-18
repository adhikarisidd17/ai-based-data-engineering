import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTrigger } from '@/components/ui/dialog';
import axios from 'axios';
import { Loader2 } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

// Shape of the preview response: adapt as-needed
interface FileChange {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  patch: string;
}
interface PRData {
  title?: string;
  body?: string;
  files?: FileChange[];
  [key: string]: any;
}

export default function PRPreview({ requestId }: { requestId: string }) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [prData, setPrData] = useState<PRData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setPrData(null);
      setError(null);
      fetchPRPreview();
    }
  }, [open, requestId]);

  async function fetchPRPreview() {
    setLoading(true);
    try {
      const url = `http://localhost:8000/preview/${requestId}`;
      const res = await axios.get<PRData>(url);
      setPrData(res.data);
    } catch (err: any) {
      if (!err.response) {
        setError('Unable to reach server.');
      } else {
        setError(err.response.data?.message || err.message);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">Preview PR</Button>
      </DialogTrigger>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold">Pull Request Preview</h3>
          </CardHeader>
          <CardContent className="space-y-4">
            {loading && (
              <div className="flex justify-center py-6">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              </div>
            )}
            {error && <p className="text-red-500">{error}</p>}

            {!loading && !error && !prData && (
              <p className="text-gray-500">No preview available.</p>
            )}

            {prData && (
              <div className="space-y-6">
                {prData.title && (
                  <h4 className="text-xl font-bold">{prData.title}</h4>
                )}
                {prData.body && (
                  <p className="whitespace-pre-wrap text-gray-700">
                    {prData.body}
                  </p>
                )}

                {prData.files?.map((file) => (
                  <Card key={file.filename} className="bg-gray-50">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-sm">{file.filename}</span>
                        <div className="flex space-x-2">
                          <Badge variant="outline" className="border-green-500 text-green-600">
                            +{file.additions}
                          </Badge>
                          <Badge variant="outline" className="border-red-500 text-red-600">
                            -{file.deletions}
                          </Badge>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="bg-white p-4 rounded shadow-inner overflow-auto text-xs font-mono">
                        {file.patch.split(/\r?\n/).map((line, idx) => {
                          const bgClass =
                            line.startsWith('+')
                              ? 'bg-green-100'
                              : line.startsWith('-')
                              ? 'bg-red-100'
                              : '';
                          return (
                            <div key={idx} className={`${bgClass} whitespace-pre-wrap`}> 
                              {line}
                            </div>
                          );
                        })}
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {/* Fallback raw data */}
                {!prData.files && (
                  <pre className="bg-gray-100 p-4 rounded text-sm font-mono overflow-auto">
                    {JSON.stringify(prData, null, 2)}
                  </pre>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </DialogContent>
    </Dialog>
  );
}
