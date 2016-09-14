#!/usr/bin/perl

use strict;
use utf8;
use CGI;
use CGI::Cookie;
use DBI;
use lib ('/home/takahashi/perl/local/lib/perl5');
use HTML::Template;
use HTML::Entities;
use Encode;
use Data::Dumper;
use DateTime;
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';
require 'timeline.pl';

sub page_operator {
	# Config
	my $SEARCH_PAGE_TMPL_PATH = '../tmpl/searchpage.tmpl';

	# Init
	my $CGI = CGI->new();

	# Get cookie
	my $user_name =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_name')));
	my $user_password =  HTML::Entities::encode_entities(decode_utf8($CGI->cookie('user_password')));

	# Get param
	my $search_text =  HTML::Entities::encode_entities(decode_utf8($CGI->param('text')));

	# Set head
	my $status_code = '';
	my $mode;
	if(!(defined $CGI->param('text'))){
		$status_code = '403';
		$mode = 'fail';
	}else{
		$status_code = '200';
		$mode = 'showPage';
	}
	my @HEADER = (
			-type => 'text/html',
			-charset => "utf-8",
			-status => $status_code
		);

	# Body
	if($mode eq 'showPage'){
		# Connect DBI
		my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',
		{
			mysql_enable_utf8 => 1
		});
		my $sth;
		my $result;
		my $is_login = 0;
		my $user_id = '';
		if(defined $CGI->cookie('user_name') && defined $CGI->cookie('user_password')){
			# Login Check
			$sth = $dbh->prepare('SELECT COUNT(*), id FROM user WHERE mail = ? AND password = ?');
			$sth->execute($user_name, $user_password);
			$result = $sth->fetchall_arrayref(+{});
			my $isPasswordDuplicate = $result->[0]->{'COUNT(*)'};
			# パスワードが間違っていたら400
			if($isPasswordDuplicate eq '0'){
				push @HEADER , ('-status', '400');
				print $CGI->header(@HEADER);
				return;
			}else{
				$is_login = 1;
				$user_id = $result->[0]->{'id'};
			}
		}
		# メインページを表示
		# Load tmpl
		my $search_page_tmpl = HTML::Template->new(
			filename => $SEARCH_PAGE_TMPL_PATH,
			utf8 => 1
		);
		# Get tweet
		$sth = $dbh->prepare('SELECT tweet.id as id, tweet.user_id as user_id, tweet.text as text, tweet.time as time, user.mail as mail FROM tweet LEFT JOIN user ON tweet.user_id = user.id WHERE tweet.text LIKE ? ORDER BY time DESC LIMIT 10');
		$sth->execute('%'.HTML::Entities::decode_entities(encode_utf8($search_text)).'%');
		$result = $sth->fetchall_arrayref(+{});
		# Make TimeLine
		my $timeline_tmpl = makeTimeLine($result, ($is_login == 1)? $user_id : '');
		$search_page_tmpl->param('TIMELINE_TMPL' => $timeline_tmpl->output);
		# Set Header
		print $CGI->header(@HEADER), $search_page_tmpl->output;
	}elsif($mode eq 'fail'){
		print $CGI->header(@HEADER);
	}

}

page_operator();
