from taskw import TaskWarriorShellout


class TwCurrent(object):

    def __init__(self, file=None):
        self.tw = TaskWarriorShellout()
        self.tw.config_filename = file

    def get_current(self):
        tw = TaskWarriorShellout()
        tw.config_filename = self.tw.config_filename
        tasks = tw.filter_tasks({'tags.contains': 'current'})
        current = tasks[0]
        return current

    def set_current(self, id):
        tasks = self.tw.filter_tasks({'tags.contains': 'current'})
        for task in tasks:
            task['tags'].remove('current')
            self.tw.task_update(task)
        id, task = self.tw.get_task()
        try:
            task['tags'].extend('current')
        except KeyError:
            task['tags'] = ['current']
        self.tw.task_update(task)

    def get_pending(self):
        tasks = self.tw.filter_tasks({'status': 'pending'})
        return tasks

if __name__ == '__main__':
    tw = TwCurrent()
    tw.get_current()
