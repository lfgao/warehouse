class Block():
    def __init__(self, node_name, qty, parent = None, child = None, is_src = False):
        self.node_name = node_name
        self.qty = qty
        self.parent = None
        self.child = None
        
        if is_src:
            self.parent = 'SRC'
        elif parent is not None:
            self.add_parent(parent)
            
        if child is not None:
            self.add_child(child)
            
    def is_src(self):
        return self.parent == 'SRC'
    
    def set_to_src(self):
        #Set self as source
        if self.parent is not None:
            raise Warning('Cannot set to source with existing parent')
        self.parent = 'SRC'
        
    def update_qty(self, newqty):
        self.qty = newqty
        
    def add_parent(self, parent_block):
        #Add a two way link to a parent block 
        if (self.parent is not None) or (parent_block.child is not None):
            raise Warning('Error')
        elif self.qty != parent_block.qty:
            raise Warning('Not matching qty')
        parent_block.child = self
        self.parent = parent_block
    
    def add_child(self, child_block):
        #Add a two way link to a child block
        if (self.child is not None) or (child_block.parent is not None):
            raise Warning('Error')
        elif self.qty != child_block.qty:
            raise Warning('Not matching qty')
        child_block.parent = self
        self.child = child_block
    
    def get_source_block(self):
        if self.is_src() or (self.parent is None):
            return self
        else:
            return self.parent.get_source_block()
    
    def get_end_block(self):
        #Traverse the childs
        if self.child is None:
            return self
        else:
            return self.child.get_end_block()
        
    def get_qty(self):
        #Returns net qty of this block
        #Positive = flow into block
        #Negative = flow out of block
        if (self.parent is not None) and (self.child is not None):
            return 0
        elif self.parent is not None:
            #Has parent no child
            return self.qty
        elif self.child is not None:
            #Has child no parent
            return -self.qty
        else:
            raise Warning('No parent and child!')
            
def get_rx_qty(block):
    #Given a block, return qty to be matched if it were to recieve new flow
    if block is not None:
        if (block.child is not None) and (block.parent is None):
            #Has child but no parent, match this much quantity
            return block.qty
    return None

def get_tx_qty(block):
    #Given a block, return qty to be matched if it were to send new flow
    if block is not None:
        if (block.parent is not None) and (block.child is None):
            #Has parent but no child, will match the flow
            return block.qty
    return None

def update_and_add(dict_, key_, val_):
    if not key_ in dict_:
        dict_[key_] = val_
    else:
        dict_[key_] += val_
        
class Graph():
    def __init__(self):
        self.nodes = {}
        pass
    
    def add_node(self, nodename):
        if nodename in self.nodes:
            raise Warning('Node already exists')
        self.nodes[nodename] = []
    
    def split_parents(self, block, new_qty):
        #Given a block and a quantity, split the block and all its parents into two blocks
        if block.child is not None:
            raise Warning('Cannot split parent with child existing')
        if (new_qty >= block.qty) or (new_qty <= 0):
            raise Warning('Invalid split quantity')
        remain_qty = block.qty - new_qty

        curblock = block
        prev_newblock = None
        while curblock is not None:
            curnodename = curblock.node_name
            curnode = self.nodes[curnodename] #List of blocks of the current node
            curblock.update_qty(remain_qty) #Shrink current node's quantity
            #Create a new split block and insert into front of current block, link child to prev_newblock
            newblock = Block(curnodename, new_qty, child = prev_newblock, is_src = curblock.is_src())
            curnode.insert(curnode.index(curblock), newblock)
            prev_newblock = newblock
            if curblock.is_src():
                break
            curblock = curblock.parent
            
    def split_children(self, block, new_qty):
        #Given a block and a quantity, split the block and all its children into two blocks
        if block.parent is not None:
            raise Warning('Cannot split child with parent existing')
        if (new_qty >= block.qty) or (new_qty <= 0):
            raise Warning('Invalid split quantity')
        remain_qty = block.qty - new_qty

        curblock = block
        prev_newblock = None
        while curblock is not None:
            curnodename = curblock.node_name
            curnode = self.nodes[curnodename] #List of blocks of the current node
            curblock.update_qty(remain_qty) #Shrink current node's quantity
            #Create a new split block and insert into front of current block, link parent to prev_newblock
            newblock = Block(curnodename, new_qty, parent = prev_newblock) 
            curnode.insert(curnode.index(curblock), newblock)
            prev_newblock = newblock
            curblock = curblock.child
            
    def get_first_block(self, node_name):
        #gvien a node, return the first non-matched block
        for curblock in self.nodes[node_name]:
            if (curblock.parent is None) or (curblock.child is None):
                return curblock
        return None
    
    def add_block(self, node, qty, is_src = False):
        newblock = Block(node, qty, is_src = is_src)
        self.nodes[node].append(newblock)
        return newblock
        
    def add_source(self, node_name, qty):
        if not node_name in self.nodes:
            self.add_node(node_name)
        
        if qty < 0:
            raise Warning('Cannot have negative quantity')
        qty_remain = qty
        while qty_remain > 0:
            curblock = self.get_first_block(node_name)
            rx_qty = get_rx_qty(curblock)
            if rx_qty is None:
                #Append a new block to the end of current block
                curqty = qty_remain
                self.add_block(node_name, qty_remain, is_src = True)
            elif rx_qty <= qty_remain:
                curblock.set_to_src()
                curqty = rx_qty
            else:
                #qty_remain < rx_qty, need to split the current block
                self.split_children(curblock, qty_remain)
                curqty = 0
            qty_remain = qty_remain - curqty
            
            
    def transact(self, from_node, to_node, qty):
        if qty < 0:
            raise Warning('Cannot have negative quantity')
        if from_node not in self.nodes:
            self.add_node(from_node)
        if to_node not in self.nodes:
            self.add_node(to_node)
            
        qty_remain = qty
        while qty_remain > 0:
            from_block = self.get_first_block(from_node)
            to_block = self.get_first_block(to_node)
            
            tx_qty = get_tx_qty(from_block) #Quantity to be transfered out
            rx_qty = get_rx_qty(to_block) #Quantity to be transfered to 
            min_qty = min([x for x in [tx_qty, rx_qty, qty_remain] if x is not None])

            if tx_qty is not None:
                if tx_qty > min_qty:
                    self.split_parents(from_block, min_qty)
                    continue
            if rx_qty is not None:
                if rx_qty > min_qty:
                    self.split_children(to_block, min_qty)
                    continue
            #At this stage, there should be no need for splitting
            
            if tx_qty is None:
                #Create a new block for tx
                from_block = self.add_block(from_node, min_qty)
            if rx_qty is None:
                #Create a new block for rx
                to_block = self.add_block(to_node, min_qty)
                
            from_block.add_child(to_block)
            qty_remain = qty_remain - min_qty
            
    def show_inventory(self):
        for curnode in sorted(self.nodes.keys()):
            chain = []
            for curblock in self.nodes[curnode]:
                qty = str(curblock.qty)
                if curblock.get_qty() == 0:
                    qty = 'E' + qty
                elif curblock.get_qty() > 0:
                    qty = '+' + qty
                elif curblock.get_qty() < 0:
                    qty = '-' + qty
                if curblock.is_src():
                    qty = qty + '*'
                chain.append(qty)
            tot_qty = sum([x.get_qty() for x in self.nodes[curnode]])
            print('%s(%d): %s'%(curnode, tot_qty, ','.join(chain)))
            
    def show_source_detailed(self, node):
        for curblock in self.nodes[node]:
            path = []
            qty = curblock.get_qty()
            if qty < 0:
                raise Warning('Unmatched!')
            elif qty == 0:
                continue
                
            while (curblock is not None):
                curnode = curblock.node_name
                if curblock.is_src():
                    curnode += '*'
                    curblock = None
                else:
                    curblock = curblock.parent
                path.append(curnode)
            print('%d : %s'%(qty, ' <== '.join(path)))
    def get_node_qty(self, node):
        return sum([x.get_qty() for x in self.nodes[node]])
    def show_source(self, node):
        matched = {}
        unmatched = {}
        for curblock in self.nodes[node]:
            if curblock.get_qty() == 0:
                continue
            srcblock = curblock.get_source_block()
            if srcblock.is_src():
                update_and_add(matched, srcblock.node_name, srcblock.qty)
            else:
                update_and_add(unmatched, srcblock.node_name, srcblock.qty)
        if len(matched) > 0:
            print('%s[matched]: %s'%(node, ', '.join(['%d(%s)'%(value, key) for key, value in matched.items()])))

        if len(unmatched) > 0:
            print('%s[unmatched]: %s'%(node, ', '.join(['%d(%s)'%(value, key) for key, value in unmatched.items()])))            
            
    def show_dispense(self, node):
        children = {}
        for curblock in self.nodes[node]:
            endblock = curblock.get_end_block()
            update_and_ad(childs, endblock.node_name, endblock.qty)
        print('Child nodes:')
        print(', '.join(['%d %s'%(value, key) for key, value in children.items()]))
        
    def show_all_source(self):
        for curnodename in self.nodes:
            self.show_source(curnodename)
            
a = Graph()
a.add_source('A001', 100)
a.add_source('A002', 100)
a.add_source('A003', 100)
a.transact('A001','A004', 100)
a.transact('A002','A004', 100)
a.transact('A003','A005', 20)
a.transact('A003','A006', 80)
a.transact('A004','A007',40)
a.transact('A004','A008', 160)
a.transact('A005','A008', 20)
a.transact('A006','A008',80)
a.transact('A007','A009', 40)
a.transact('A008', 'A009', 60)
a.transact('A008','A010', 100)
a.transact('A008','A011', 100)
a.show_inventory()
print("\nShowing source summary")
a.show_all_source()
print("\nShowing detailed path")

for curnode in a.nodes:
    if a.get_node_qty(curnode) > 0:
        print('---------- %s ---------'%curnode)
        a.show_source_detailed(curnode)
