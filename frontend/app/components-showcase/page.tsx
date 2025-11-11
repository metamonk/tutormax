"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle, CardAction } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Checkbox } from "@/components/ui/checkbox"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert"
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar } from "@/components/ui/avatar"
import { Progress } from "@/components/ui/progress"
import { Separator } from "@/components/ui/separator"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { ThemeToggle } from "@/components/theme-toggle"
import { AlertCircle, CheckCircle2, Info, Loader2, XCircle } from "lucide-react"

export default function ComponentShowcase() {
  return (
    <div className="container mx-auto py-10 space-y-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold">Component Showcase</h1>
          <p className="text-muted-foreground mt-2">
            Testing all shadcn/ui components with fintech design system
          </p>
        </div>
        <ThemeToggle />
      </div>

      <Separator />

      {/* Buttons Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Buttons</h2>
        <Card>
          <CardHeader>
            <CardTitle>Button Variants</CardTitle>
            <CardDescription>All button styles and sizes</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-4 items-center">
              <Button>Default</Button>
              <Button variant="secondary">Secondary</Button>
              <Button variant="destructive">Destructive</Button>
              <Button variant="outline">Outline</Button>
              <Button variant="ghost">Ghost</Button>
              <Button variant="link">Link</Button>
            </div>
            <div className="flex flex-wrap gap-4 items-center">
              <Button size="sm">Small</Button>
              <Button size="default">Default</Button>
              <Button size="lg">Large</Button>
              <Button size="icon">
                <Info className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex flex-wrap gap-4 items-center">
              <Button disabled>Disabled</Button>
              <Button loading>Loading</Button>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Form Inputs Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Form Inputs</h2>
        <Card>
          <CardHeader>
            <CardTitle>Input Components</CardTitle>
            <CardDescription>Text inputs, selects, checkboxes, and radios</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="input-normal">Normal Input</Label>
              <Input id="input-normal" placeholder="Enter text..." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="input-disabled">Disabled Input</Label>
              <Input id="input-disabled" placeholder="Disabled" disabled />
            </div>
            <div className="space-y-2">
              <Label htmlFor="input-error">Error State</Label>
              <Input id="input-error" placeholder="Invalid input" aria-invalid />
            </div>
            <div className="space-y-2">
              <Label htmlFor="textarea">Textarea</Label>
              <Textarea id="textarea" placeholder="Enter long text..." />
            </div>
            <div className="space-y-2">
              <Label htmlFor="select">Select</Label>
              <Select>
                <SelectTrigger id="select">
                  <SelectValue placeholder="Select an option" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="option1">Option 1</SelectItem>
                  <SelectItem value="option2">Option 2</SelectItem>
                  <SelectItem value="option3">Option 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2">
              <Checkbox id="checkbox" />
              <Label htmlFor="checkbox">Accept terms and conditions</Label>
            </div>
            <RadioGroup defaultValue="option1">
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="option1" id="radio1" />
                <Label htmlFor="radio1">Option 1</Label>
              </div>
              <div className="flex items-center space-x-2">
                <RadioGroupItem value="option2" id="radio2" />
                <Label htmlFor="radio2">Option 2</Label>
              </div>
            </RadioGroup>
          </CardContent>
        </Card>
      </section>

      {/* Cards Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Cards</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Simple Card</CardTitle>
              <CardDescription>A basic card with title and description</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">This is the card content area.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Card with Action</CardTitle>
              <CardDescription>Card with an action button in header</CardDescription>
              <CardAction>
                <Button size="sm" variant="ghost">Edit</Button>
              </CardAction>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Content with header action</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Card with Footer</CardTitle>
              <CardDescription>Card with footer actions</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">This card has footer buttons</p>
            </CardContent>
            <CardFooter className="gap-2">
              <Button variant="outline" size="sm">Cancel</Button>
              <Button size="sm">Save</Button>
            </CardFooter>
          </Card>
        </div>
      </section>

      {/* Badges Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Badges</h2>
        <Card>
          <CardHeader>
            <CardTitle>Badge Variants</CardTitle>
            <CardDescription>Status indicators and labels</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              <Badge>Default</Badge>
              <Badge variant="secondary">Secondary</Badge>
              <Badge variant="destructive">Destructive</Badge>
              <Badge variant="outline">Outline</Badge>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Alerts Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Alerts</h2>
        <div className="space-y-4">
          <Alert>
            <Info className="h-4 w-4" />
            <AlertTitle>Information</AlertTitle>
            <AlertDescription>
              This is an informational alert message.
            </AlertDescription>
          </Alert>
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>
              This is a destructive/error alert message.
            </AlertDescription>
          </Alert>
        </div>
      </section>

      {/* Tables Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Tables</h2>
        <Card>
          <CardHeader>
            <CardTitle>Data Table</CardTitle>
            <CardDescription>Example table with hover states</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableCaption>A list of recent transactions</TableCaption>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow>
                  <TableCell>001</TableCell>
                  <TableCell>John Doe</TableCell>
                  <TableCell>
                    <Badge>Active</Badge>
                  </TableCell>
                  <TableCell className="text-right">$250.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>002</TableCell>
                  <TableCell>Jane Smith</TableCell>
                  <TableCell>
                    <Badge variant="secondary">Pending</Badge>
                  </TableCell>
                  <TableCell className="text-right">$150.00</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>003</TableCell>
                  <TableCell>Bob Johnson</TableCell>
                  <TableCell>
                    <Badge variant="destructive">Failed</Badge>
                  </TableCell>
                  <TableCell className="text-right">$350.00</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </section>

      {/* Tabs Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Tabs</h2>
        <Card>
          <CardHeader>
            <CardTitle>Tab Component</CardTitle>
            <CardDescription>Tabbed content navigation</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="tab1">
              <TabsList>
                <TabsTrigger value="tab1">Overview</TabsTrigger>
                <TabsTrigger value="tab2">Details</TabsTrigger>
                <TabsTrigger value="tab3">Settings</TabsTrigger>
              </TabsList>
              <TabsContent value="tab1" className="mt-4">
                <p className="text-sm text-muted-foreground">Overview content goes here</p>
              </TabsContent>
              <TabsContent value="tab2" className="mt-4">
                <p className="text-sm text-muted-foreground">Details content goes here</p>
              </TabsContent>
              <TabsContent value="tab3" className="mt-4">
                <p className="text-sm text-muted-foreground">Settings content goes here</p>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </section>

      {/* Progress Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Progress</h2>
        <Card>
          <CardHeader>
            <CardTitle>Progress Indicators</CardTitle>
            <CardDescription>Loading and progress states</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>25% Complete</Label>
              <Progress value={25} />
            </div>
            <div className="space-y-2">
              <Label>50% Complete</Label>
              <Progress value={50} />
            </div>
            <div className="space-y-2">
              <Label>75% Complete</Label>
              <Progress value={75} />
            </div>
          </CardContent>
        </Card>
      </section>

      {/* Dialog Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Dialogs</h2>
        <Card>
          <CardHeader>
            <CardTitle>Modal Dialogs</CardTitle>
            <CardDescription>Overlay dialogs and modals</CardDescription>
          </CardHeader>
          <CardContent>
            <Dialog>
              <DialogTrigger asChild>
                <Button>Open Dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Are you sure?</DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. This will permanently delete your account
                    and remove your data from our servers.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <Button variant="outline">Cancel</Button>
                  <Button variant="destructive">Delete Account</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </CardContent>
        </Card>
      </section>

      {/* Loading States Section */}
      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Loading States</h2>
        <Card>
          <CardHeader>
            <CardTitle>Loading Indicators</CardTitle>
            <CardDescription>Various loading state patterns</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm">Loading...</span>
            </div>
            <div className="skeleton h-4 w-full rounded" />
            <div className="skeleton h-4 w-3/4 rounded" />
            <div className="skeleton h-4 w-1/2 rounded" />
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
