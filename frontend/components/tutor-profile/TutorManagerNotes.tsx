'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ManagerNoteItem } from '@/lib/types';
import { StickyNote, Star } from 'lucide-react';

interface TutorManagerNotesProps {
  notes: ManagerNoteItem[];
}

export function TutorManagerNotes({ notes }: TutorManagerNotesProps) {
  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (notes.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Manager Notes</CardTitle>
          <CardDescription>No notes yet</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center text-muted-foreground">
            <StickyNote className="h-12 w-12 mb-4 opacity-50" />
            <p>No manager notes available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Manager Notes</CardTitle>
        <CardDescription>{notes.length} note{notes.length !== 1 ? 's' : ''}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {notes.map((note) => (
            <div
              key={note.note_id}
              className={`p-4 border rounded-lg ${note.is_important ? 'border-orange-500 bg-orange-50 dark:bg-orange-950/20' : ''}`}
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-sm">{note.author_name}</p>
                  {note.is_important && (
                    <Badge variant="destructive" className="flex items-center gap-1">
                      <Star className="h-3 w-3" />
                      Important
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-muted-foreground">{formatDate(note.created_at)}</p>
              </div>
              <p className="text-sm whitespace-pre-wrap">{note.note_text}</p>
              {note.updated_at !== note.created_at && (
                <p className="text-xs text-muted-foreground mt-2 italic">
                  Updated: {formatDate(note.updated_at)}
                </p>
              )}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
