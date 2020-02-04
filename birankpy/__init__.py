import networkx as nx
import pandas as pd
import numpy as np
import scipy
import scipy.sparse as spa


class BipartiteNetwork:
    """
    Class for handling bipartite networks using scipy's sparse matrix
    Design to for large networkx, but functionalities are limited
    """
    def __init__(self):
        pass

    def load_edgelist(
        self, edgelist_path, top_col, bottom_col,
        weight_col='None', sep=','
    ):
        """
        Method to load the edgelist.

        Input:
            edge_list_path::string: the path to the edgelist file
            top_col::string: column of the top nodes
            bottom_col::string: column of the bottom nodes
            weight_col::string: column of the edge weights
            sep::string: the seperators of the edgelist file


        Suppose the bipartite network has D top nodes and
        P bottom nodes.
        The edgelist file should have the format similar to the example:

        top,bottom,weight
        t1,b1,1
        t1,b2,1
        t2,b1,2
        ...
        tD,bP,1

        The edgelist file needs at least two columns for the top nodes and
        bottom nodes. An optional column can carry the edge weight.
        You need to specify the columns in the method parameters.

        The network is represented by a D*P dimensional matrix.
        """

        temp_df = pd.read_csv(edgelist_path, sep=sep)
        self.set_edgelist(temp_df, top_col, bottom_col, weight_col)

    def set_edgelist(self, df, top_col, bottom_col, weight_col=None):
        """
        Method to set the edgelist.

        Input:
            df::pandas.DataFrame: the edgelist with at least two columns
            top_col::string: column of the edgelist dataframe for top nodes
            bottom_col::string: column of the edgelist dataframe for bottom nodes
            weight_col::string: column of the edgelist dataframe for edge weights

        The edgelist should be represented by a dataframe.
        The dataframe eeds at least two columns for the top nodes and
        bottom nodes. An optional column can carry the edge weight.
        You need to specify the columns in the method parameters.
        """
        self.df = df
        self.top_col = top_col
        self.bottom_col = bottom_col
        self.weight_col = weight_col

        self._index_nodes()
        self._generate_adj()

    def _index_nodes(self):
        """
        Representing the network with adjacency matrix requires indexing the top
        and bottom nodes first
        """
        self.top_ids = pd.DataFrame(
            self.df[self.top_col].unique(),
            columns=[self.top_col]
        ).reset_index()
        self.top_ids = self.top_ids.rename(columns={'index': 'top_index'})

        self.bottom_ids = pd.DataFrame(
            self.df[self.bottom_col].unique(),
            columns=[self.bottom_col]
        ).reset_index()
        self.bottom_ids = self.bottom_ids.rename(columns={'index': 'bottom_index'})

        self.df = self.df.merge(self.top_ids, on=self.top_col)
        self.df = self.df.merge(self.bottom_ids, on=self.bottom_col)

    def _generate_adj(self):
        """
        Generating the adjacency matrix for the birparite network.
        The matrix has dimension: D * P where D is the number of top nodes
        and P is the number of bottom nodes
        """
        if self.weight_col is None:
            # set weight to 1 if weight column is not present
            weight = np.ones(len(self.df))
        else:
            weight = self.df[self.weight_col]
        self.W = spa.coo_matrix(
            (
                weight,
                (self.df['top_index'].values, self.df['bottom_index'].values)
            )
        )

    def unipartite_projection(self, on):
        """
        Project the bipartite network to one side of the nodes
        to generate a unipartite network

        Input:
            on::string: top or bottom

        If projected on top nodes, the resulting adjacency matrix has
        dimension: D*D
        If projected on bottom nodes, the resulting adjacency matrix
        has dimension: P*P
        """
        if on == self.bottom_col:
            self.unipartite_adj = self.W.T.dot(self.W)
        else:
            self.unipartite_adj = self.W.dot(self.W.T)

        self.unipartite_adj.setdiag(0)
        self.unipartite_adj.eliminate_zeros()

        if on == self.bottom_col:
            return self.bottom_ids, self.unipartite_adj
        else:
            return self.top_ids, self.unipartite_adj

    def generate_degree(self):
        """
        This method returns the degree of nodes in the bipartite network
        """
        top_df = self.df.groupby(self.top_col)[self.bottom_col].nunique()
        top_df = top_df.to_frame(name='degree').reset_index()
        bottom_df = self.df.groupby(self.bottom_col)[self.top_col].nunique()
        bottom_df = bottom_df.to_frame(name='degree').reset_index()
        return top_df, bottom_df