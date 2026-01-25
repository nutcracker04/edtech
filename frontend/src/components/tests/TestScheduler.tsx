import { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Clock, Calendar as CalendarIcon, Bell } from 'lucide-react';
import { format } from 'date-fns';
import { cn } from '@/lib/utils';

interface TestSchedulerProps {
  testTitle: string;
  testDuration: number;
  onSchedule: (scheduledDate: Date) => void;
  onCancel: () => void;
}

export function TestScheduler({ testTitle, testDuration, onSchedule, onCancel }: TestSchedulerProps) {
  const [date, setDate] = useState<Date | undefined>(new Date());
  const [hour, setHour] = useState<string>('09');
  const [minute, setMinute] = useState<string>('00');
  const [reminderEnabled, setReminderEnabled] = useState(true);
  const [reminderTime, setReminderTime] = useState<string>('30'); // minutes before

  const hours = Array.from({ length: 24 }, (_, i) => i.toString().padStart(2, '0'));
  const minutes = ['00', '15', '30', '45'];
  const reminderOptions = [
    { value: '15', label: '15 minutes before' },
    { value: '30', label: '30 minutes before' },
    { value: '60', label: '1 hour before' },
    { value: '1440', label: '1 day before' },
  ];

  const handleSchedule = () => {
    if (!date) return;

    const scheduledDate = new Date(date);
    scheduledDate.setHours(parseInt(hour));
    scheduledDate.setMinutes(parseInt(minute));
    scheduledDate.setSeconds(0);

    onSchedule(scheduledDate);
  };

  const getFormattedDateTime = () => {
    if (!date) return '';
    const tempDate = new Date(date);
    tempDate.setHours(parseInt(hour));
    tempDate.setMinutes(parseInt(minute));
    return format(tempDate, 'PPP p');
  };

  const isDateInPast = () => {
    if (!date) return false;
    const tempDate = new Date(date);
    tempDate.setHours(parseInt(hour));
    tempDate.setMinutes(parseInt(minute));
    return tempDate < new Date();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold">Schedule Test</h2>
        <p className="text-muted-foreground mt-1">
          {testTitle} • Duration: {testDuration} minutes
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Calendar */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <CalendarIcon className="h-5 w-5" />
              Select Date
            </CardTitle>
            <CardDescription>Choose when you want to take the test</CardDescription>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Calendar
              mode="single"
              selected={date}
              onSelect={setDate}
              disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
              className="rounded-md border"
            />
          </CardContent>
        </Card>

        {/* Time and Settings */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Select Time
              </CardTitle>
              <CardDescription>Choose the start time</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Hour</Label>
                  <Select value={hour} onValueChange={setHour}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="max-h-[200px]">
                      {hours.map((h) => (
                        <SelectItem key={h} value={h}>
                          {h}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label>Minute</Label>
                  <Select value={minute} onValueChange={setMinute}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {minutes.map((m) => (
                        <SelectItem key={m} value={m}>
                          {m}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {isDateInPast() && (
                <p className="text-sm text-red-600">
                  Selected time is in the past. Please choose a future time.
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Bell className="h-5 w-5" />
                Reminder
              </CardTitle>
              <CardDescription>Get notified before the test</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="reminder-toggle">Enable reminder</Label>
                <Button
                  id="reminder-toggle"
                  variant={reminderEnabled ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setReminderEnabled(!reminderEnabled)}
                >
                  {reminderEnabled ? 'On' : 'Off'}
                </Button>
              </div>

              {reminderEnabled && (
                <div className="space-y-2">
                  <Label>Remind me</Label>
                  <Select value={reminderTime} onValueChange={setReminderTime}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {reminderOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Summary */}
      {date && (
        <Card className="border-primary/50 bg-primary/5">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">Scheduled for:</p>
                <p className="text-2xl font-bold text-primary mt-1">{getFormattedDateTime()}</p>
                {reminderEnabled && (
                  <p className="text-sm text-muted-foreground mt-2">
                    You'll receive a reminder {reminderOptions.find(o => o.value === reminderTime)?.label}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <Button variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button onClick={handleSchedule} disabled={!date || isDateInPast()}>
          Schedule Test
        </Button>
      </div>
    </div>
  );
}
