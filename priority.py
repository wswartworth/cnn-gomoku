import heapq
import itertools

'''
borrowed from Python documentation of heapq
'''

#max heap
class myPriorityQueue:

    pq = []                         # list of entries arranged in a heap
    entry_finder = {}               # mapping of tasks to entries
    REMOVED = '<removed-task>'      # placeholder for a removed task
    counter = itertools.count()     # unique sequence count

    def add_task(self, task, priority=0):
        pq = self.pq
        entry_finder = self.entry_finder
        counter = self.counter
        
        'Add a new task or update the priority of an existing task'
        if task in entry_finder:
            self.remove_task(task)
        count = next(counter)
        entry = [-priority, count, task]
        entry_finder[task] = entry
        heapq.heappush(pq, entry)

    def remove_task(self, task):
        entry_finder = self.entry_finder
        'Mark an existing task as REMOVED.  Raise KeyError if not found.'
        entry = entry_finder.pop(task)
        entry[-1] = self.REMOVED

    def pop_task(self):
        pq = self.pq
        entry_finder = self.entry_finder
        'Remove and return the lowest priority task. Raise KeyError if empty.'
        while pq:
            priority, count, task = heapq.heappop(pq)
            if task is not self.REMOVED:
                del entry_finder[task]
                return task
        raise KeyError('pop from an empty priority queue')

    #increase the priority by n
    def increase_priority(self, task, n):
        entry_finder = self.entry_finder
        if not task in entry_finder: return
        priority, count, task = entry_finder[task]
        self.add_task(task, n-priority) #funny because max heap

    def sorted_list(self):
        pq = self.pq
        REMOVED = self.REMOVED
        l = heapq.nsmallest(len(pq), pq)
        ret = []
        for entry in l:
            add = entry[2]
            if(add is not REMOVED): ret.append(add)
        return ret

    #return the list up to a given priority
    def truncated_sorted_list(self, t):
        pq = self.pq
        REMOVED = self.REMOVED
        l = heapq.nsmallest(len(pq), pq)
        ret = []
        for entry in l:
            add = entry[2]
            pri = entry[0]
            if pri >= -t: return ret
            if(add is not REMOVED): ret.append(add)
        return ret
        


#pq = myPriorityQueue()
#pq.add_task("a", 6)
#pq.add_task("b", 4)
#pq.add_task("c", 2)
#pq.add_task("d", 1)
#pq.increase_priority("d", 2)
#print(pq.sorted_list())
#print(pq.sorted_list())
#print(pq.pop_task())
#print(pq.pop_task())
#print(pq.pop_task())
#print(pq.pop_task())
