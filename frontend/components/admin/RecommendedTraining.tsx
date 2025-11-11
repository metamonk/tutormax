'use client';

/**
 * Recommended Training Component
 * Displays training modules as a Kanban board with assignment capabilities
 */

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  KanbanProvider,
  KanbanBoard,
  KanbanHeader,
  KanbanCards,
  KanbanCard,
  type DragEndEvent
} from '@/components/kibo-ui/kanban';
import {
  Tags,
  TagsTrigger,
  TagsValue,
  TagsContent,
  TagsInput,
  TagsList,
  TagsEmpty,
  TagsGroup,
  TagsItem
} from '@/components/kibo-ui/tags';
import {
  BookOpen,
  Clock,
  Users,
  Filter,
  Plus,
  Search,
  GraduationCap,
  Target
} from 'lucide-react';
import type { TrainingModule, TrainingAssignment } from '@/lib/types';
import { cn } from '@/lib/utils';

interface RecommendedTrainingProps {
  apiEndpoint?: string;
  onModuleUpdate?: (module: TrainingModule) => void;
}

// Kanban columns
const columns = [
  { id: 'to_do', name: 'To Do' },
  { id: 'in_progress', name: 'In Progress' },
  { id: 'completed', name: 'Completed' }
];

// Category colors and icons
const categoryConfig = {
  pedagogy: {
    label: 'Pedagogy',
    color: 'bg-blue-600 dark:bg-blue-500 text-white'
  },
  technology: {
    label: 'Technology',
    color: 'bg-purple-600 dark:bg-purple-500 text-white'
  },
  communication: {
    label: 'Communication',
    color: 'bg-emerald-600 dark:bg-emerald-500 text-white'
  },
  compliance: {
    label: 'Compliance',
    color: 'bg-red-600 dark:bg-red-500 text-white'
  },
  subject_matter: {
    label: 'Subject Matter',
    color: 'bg-amber-600 dark:bg-amber-500 text-white'
  }
};

export function RecommendedTraining({
  apiEndpoint = '/api/admin/training',
  onModuleUpdate
}: RecommendedTrainingProps) {
  const [modules, setModules] = useState<TrainingModule[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedPriority, setSelectedPriority] = useState<string>('');
  const [tutorFilter, setTutorFilter] = useState('');

  useEffect(() => {
    fetchTrainingModules();
  }, []);

  const fetchTrainingModules = async () => {
    setLoading(true);
    try {
      // Mock data for demonstration - replace with actual API call
      const mockModules: TrainingModule[] = [
        {
          id: '1',
          title: 'Effective Virtual Teaching Strategies',
          description: 'Learn best practices for engaging students in online learning environments',
          category: 'pedagogy',
          priority: 'high',
          estimated_duration_minutes: 120,
          status: 'to_do',
          assigned_tutors: ['T-001', 'T-003'],
          completion_rate: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          due_date: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString()
        },
        {
          id: '2',
          title: 'Zoom Advanced Features Training',
          description: 'Master breakout rooms, screen sharing, and interactive tools',
          category: 'technology',
          priority: 'medium',
          estimated_duration_minutes: 60,
          status: 'in_progress',
          assigned_tutors: ['T-002'],
          completion_rate: 45,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '3',
          title: 'Active Listening and Feedback',
          description: 'Develop communication skills for better student engagement',
          category: 'communication',
          priority: 'high',
          estimated_duration_minutes: 90,
          status: 'to_do',
          assigned_tutors: ['T-004', 'T-005'],
          completion_rate: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '4',
          title: 'FERPA and COPPA Compliance',
          description: 'Understanding student privacy laws and data protection',
          category: 'compliance',
          priority: 'high',
          estimated_duration_minutes: 45,
          status: 'completed',
          assigned_tutors: ['T-001', 'T-002', 'T-003'],
          completion_rate: 100,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '5',
          title: 'Advanced Calculus Concepts',
          description: 'Deep dive into differential equations and integration techniques',
          category: 'subject_matter',
          priority: 'medium',
          estimated_duration_minutes: 180,
          status: 'in_progress',
          assigned_tutors: ['T-006'],
          completion_rate: 60,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: '6',
          title: 'Growth Mindset in Education',
          description: 'Foster resilience and positive learning attitudes in students',
          category: 'pedagogy',
          priority: 'low',
          estimated_duration_minutes: 75,
          status: 'to_do',
          assigned_tutors: [],
          completion_rate: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];

      setModules(mockModules);
    } catch (error) {
      console.error('Failed to fetch training modules:', error);
    } finally {
      setLoading(false);
    }
  };

  // Filter modules
  const filteredModules = modules.filter(module => {
    const matchesSearch = !searchQuery ||
      module.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      module.description.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesCategory = selectedCategories.length === 0 ||
      selectedCategories.includes(module.category);

    const matchesPriority = !selectedPriority || module.priority === selectedPriority;

    const matchesTutor = !tutorFilter ||
      module.assigned_tutors.some(t => t.toLowerCase().includes(tutorFilter.toLowerCase()));

    return matchesSearch && matchesCategory && matchesPriority && matchesTutor;
  });

  // Transform for Kanban - add index signature for Kanban compatibility
  type KanbanModule = TrainingModule & {
    name: string;
    column: string;
    [key: string]: any; // Index signature for Kanban compatibility
  };

  const kanbanData: KanbanModule[] = filteredModules.map(module => ({
    ...module,
    name: module.title,
    column: module.status
  }));

  // Handle drag and drop
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeModule = modules.find(m => m.id === active.id);
    if (!activeModule) return;

    const newStatus = over.id as TrainingModule['status'];
    if (activeModule.status === newStatus) return;

    const updatedModules = modules.map(m =>
      m.id === activeModule.id
        ? { ...m, status: newStatus, completion_rate: newStatus === 'completed' ? 100 : m.completion_rate }
        : m
    );

    setModules(updatedModules);
    onModuleUpdate?.(updatedModules.find(m => m.id === activeModule.id)!);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-600 dark:bg-red-500 text-white';
      case 'medium':
        return 'bg-amber-600 dark:bg-amber-500 text-white';
      case 'low':
        return 'bg-emerald-600 dark:bg-emerald-500 text-white';
      default:
        return 'bg-slate-500 dark:bg-slate-600 text-white';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Loading training modules...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GraduationCap className="h-5 w-5" />
                Training Module Management
              </CardTitle>
              <CardDescription>
                Assign and track training modules for tutor development
              </CardDescription>
            </div>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Module
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {/* Filters */}
          <div className="space-y-4">
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search training modules..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Category Filter */}
              <Tags
                value={selectedCategories.join(',')}
                setValue={(value) => setSelectedCategories(value ? value.split(',') : [])}
              >
                <TagsTrigger>
                  {selectedCategories.map(cat => (
                    <TagsValue
                      key={cat}
                      onRemove={() => setSelectedCategories(selectedCategories.filter(c => c !== cat))}
                      className={categoryConfig[cat as keyof typeof categoryConfig]?.color}
                    >
                      {categoryConfig[cat as keyof typeof categoryConfig]?.label || cat}
                    </TagsValue>
                  ))}
                </TagsTrigger>
                <TagsContent>
                  <TagsInput placeholder="Filter by category..." />
                  <TagsList>
                    <TagsEmpty>No categories found</TagsEmpty>
                    <TagsGroup>
                      {Object.entries(categoryConfig).map(([key, config]) => (
                        <TagsItem
                          key={key}
                          value={key}
                          onSelect={() => {
                            if (selectedCategories.includes(key)) {
                              setSelectedCategories(selectedCategories.filter(c => c !== key));
                            } else {
                              setSelectedCategories([...selectedCategories, key]);
                            }
                          }}
                        >
                          <Badge className={config.color}>{config.label}</Badge>
                        </TagsItem>
                      ))}
                    </TagsGroup>
                  </TagsList>
                </TagsContent>
              </Tags>

              {/* Priority Filter */}
              <select
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background"
                value={selectedPriority}
                onChange={(e) => setSelectedPriority(e.target.value)}
              >
                <option value="">All Priorities</option>
                <option value="high">High Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="low">Low Priority</option>
              </select>

              {/* Tutor Filter */}
              <Input
                placeholder="Filter by tutor ID..."
                value={tutorFilter}
                onChange={(e) => setTutorFilter(e.target.value)}
              />
            </div>

            {/* Clear Filters */}
            {(searchQuery || selectedCategories.length > 0 || selectedPriority || tutorFilter) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setSearchQuery('');
                  setSelectedCategories([]);
                  setSelectedPriority('');
                  setTutorFilter('');
                }}
              >
                Clear All Filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Total Modules</p>
            <p className="mt-2 text-3xl font-bold">{modules.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">To Do</p>
            <p className="mt-2 text-3xl font-bold text-slate-600 dark:text-slate-400">
              {modules.filter(m => m.status === 'to_do').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">In Progress</p>
            <p className="mt-2 text-3xl font-bold text-blue-600 dark:text-blue-400">
              {modules.filter(m => m.status === 'in_progress').length}
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-6">
            <p className="text-sm font-medium text-muted-foreground">Completed</p>
            <p className="mt-2 text-3xl font-bold text-emerald-600 dark:text-emerald-400">
              {modules.filter(m => m.status === 'completed').length}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Kanban Board */}
      <Card>
        <CardContent className="p-6">
          <KanbanProvider
            columns={columns}
            data={kanbanData}
            onDataChange={(newData) => {
              // Cast back to TrainingModule array
              const updatedModules = (newData as KanbanModule[]).map(item => {
                const { name, column, ...rest } = item;
                return {
                  ...rest,
                  status: column as TrainingModule['status']
                } as TrainingModule;
              });
              setModules(updatedModules);
            }}
            onDragEnd={handleDragEnd}
            className="min-h-[600px]"
          >
            {(column) => (
              <KanbanBoard id={column.id} key={column.id}>
                <KanbanHeader className="bg-muted/50">
                  <div className="flex items-center justify-between">
                    <span>{column.name}</span>
                    <Badge variant="secondary">
                      {kanbanData.filter(m => m.column === column.id).length}
                    </Badge>
                  </div>
                </KanbanHeader>
                <KanbanCards id={column.id}>
                  {(item) => {
                    const module = item as KanbanModule;
                    return (
                      <KanbanCard
                        key={module.id}
                        id={module.id}
                        name={module.name}
                        column={module.column}
                        className="cursor-grab active:cursor-grabbing"
                      >
                        <div className="space-y-2">
                          <div className="font-medium text-sm">{module.title}</div>
                          <div className="text-xs text-muted-foreground line-clamp-2">
                            {module.description}
                          </div>

                          <div className="flex flex-wrap gap-1">
                            <Badge className={categoryConfig[module.category as keyof typeof categoryConfig]?.color}>
                              {categoryConfig[module.category as keyof typeof categoryConfig]?.label}
                            </Badge>
                            <Badge className={getPriorityColor(module.priority)}>
                              {module.priority}
                            </Badge>
                          </div>

                          <div className="flex items-center gap-4 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1">
                              <Clock className="h-3 w-3" />
                              {module.estimated_duration_minutes}m
                            </div>
                            <div className="flex items-center gap-1">
                              <Users className="h-3 w-3" />
                              {module.assigned_tutors.length}
                            </div>
                          </div>

                          {module.status === 'in_progress' && (
                            <div className="space-y-1">
                              <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Progress</span>
                                <span className="font-medium">{module.completion_rate}%</span>
                              </div>
                              <div className="w-full bg-gray-200 rounded-full h-1.5 dark:bg-gray-700">
                                <div
                                  className="bg-blue-600 h-1.5 rounded-full transition-all"
                                  style={{ width: `${module.completion_rate}%` }}
                                />
                              </div>
                            </div>
                          )}

                          {module.due_date && module.status !== 'completed' && (
                            <div className="text-xs text-orange-600 dark:text-orange-400">
                              Due: {new Date(module.due_date).toLocaleDateString()}
                            </div>
                          )}
                        </div>
                      </KanbanCard>
                    );
                  }}
                </KanbanCards>
              </KanbanBoard>
            )}
          </KanbanProvider>
        </CardContent>
      </Card>
    </div>
  );
}
