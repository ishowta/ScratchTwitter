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
use POSIX 'ceil';
binmode (STDIN,  ':utf8');
binmode (STDOUT, ':utf8');
require 'utils.cgi';

#need [{id, user_id, mail, text, time},...] , $user_id
sub makeTimeLine {
	my ($CGI, $WHERE, $WHERE_DATA_REF, $user_id) = @_;

	# Config
	my $TIMELINE_TMPL_PATH = '../tmpl/timeline.tmpl';

	# Get param
	my $page = decode_utf8($CGI->param('page')) // 1;
	if($page !~ /^[1-9][0-9]*$/){
		$page = 1;
	}

	# Load tmpl
		my $timeline_tmpl = HTML::Template->new(
		filename => $TIMELINE_TMPL_PATH,
		utf8 => 1
	);

	# Connect DBI
	my $dbh = DBI->connect('dbi:mysql:dbname=takahashi', 'www', '',{mysql_enable_utf8 => 1});

	# Count tweet
	my $sth = $dbh->prepare('SELECT COUNT(*) FROM tweet '.$WHERE);
	$sth->execute(@$WHERE_DATA_REF);
	my $raw_count_data = $sth->fetchall_arrayref(+{});
	my $tweet_count = $raw_count_data->[0]->{'COUNT(*)'};

	# Get tweet
	$sth = $dbh->prepare('SELECT tweet.pic as pic, tweet.id as id, tweet.user_id as user_id, tweet.text as text, tweet.time as time, user.mail as mail, user.icon as icon, tweet.retweet_id as retweet_id FROM tweet LEFT JOIN user ON tweet.user_id = user.id '.$WHERE.' ORDER BY time DESC LIMIT ?, 15');
	my @buff = @$WHERE_DATA_REF;
	push @buff, ($page-1) * 15;
	$sth->execute(@buff);
	my $data = $sth->fetchall_arrayref(+{});

	# Disconnect DBI
	$dbh->disconnect;

	# Put Tweet
	my @tweets = ();
	foreach my $raw_tweet (@$data){
		my $_tweet = $raw_tweet->{'text'};
		my $encoded_text = ($_tweet);
		$encoded_text =~ s/\r\n/<br>/g;
		my %tweet = (	'USER_HREF' => '<a href="userpage.cgi?user_id='.$raw_tweet->{'user_id'}.'">'.HTML::Entities::encode_entities($raw_tweet->{'mail'}).'</a>',
						'TEXT'      => $encoded_text,
						'TIME'      => $raw_tweet->{'time'},
						'PIC'       => HTML::Entities::encode_entities($raw_tweet->{'pic'} // ''),
						'ICON'      => HTML::Entities::encode_entities($raw_tweet->{'icon'} // '')
					);
		if($raw_tweet->{'user_id'} eq $user_id){
			$tweet{'ERASE_TWEET_ZONE'} = '<a href="delete.cgi?id='.$raw_tweet->{'id'}.'" class="close"><span class="glyphicon glyphicon-remove text-danger"></span></a>';
		}else{
			$tweet{'RETWEET_ZONE'} = '<a href="tweet.cgi?retweet=1&retweet_id='.$raw_tweet->{'id'}.'" class="close">Retweet!</a>';
		}

		# Disp Retweet
		if(defined($raw_tweet->{'retweet_id'})){
			$tweet{'RETWEET_MODE'} = 1;

			my $retweet_id = $raw_tweet->{'retweet_id'};
			# Get tweet
			my $sth = $dbh->prepare('SELECT tweet.pic as pic, tweet.id as id, tweet.user_id as user_id, tweet.text as text, tweet.time as time, user.mail as mail, user.icon as icon, tweet.retweet_id as retweet_id FROM tweet LEFT JOIN user ON tweet.user_id = user.id WHERE tweet.id = ?');
			$sth->execute($retweet_id);
			my $data = $sth->fetchall_arrayref(+{});

			# Disconnect DBI
			$dbh->disconnect;

			# Put Tweet
			my @tweets = ();
			foreach my $raw_tweet (@$data){
				my $_tweet = $raw_tweet->{'text'};
				my $encoded_text = ($_tweet);
				$encoded_text =~ s/\r\n/<br>/g;
				my %tweet = (	'R_USER_HREF' => '<a href="userpage.cgi?user_id='.$raw_tweet->{'user_id'}.'">'.HTML::Entities::encode_entities($raw_tweet->{'mail'}).'</a>',
								'R_TEXT'      => $encoded_text,
								'R_TIME'      => $raw_tweet->{'time'},
								'R_PIC'       => HTML::Entities::encode_entities($raw_tweet->{'pic'} // ''),
								'R_ICON'      => HTML::Entities::encode_entities($raw_tweet->{'icon'} // '')
							);
				if($raw_tweet->{'user_id'} eq $user_id){
					$tweet{'R_ERASE_TWEET_ZONE'} = '<a href="delete.cgi?id='.$raw_tweet->{'id'}.'" class="close"><span class="glyphicon glyphicon-remove text-danger"></span></a>';
				}else{
					$tweet{'R_RETWEET_ZONE'} = '<a href="tweet.cgi?retweet=1&retweet_id='.$raw_tweet->{'id'}.'" class="close">Retweet!</a>';
				}

				# Disp ReRetweet
				if(defined($raw_tweet->{'retweet_id'})){
					my $retweet_id = $raw_tweet->{'retweet_id'};
					# Get name
					my $sth = $dbh->prepare('SELECT user.mail as mail FROM tweet LEFT JOIN user ON tweet.user_id = user.id WHERE tweet.id = ?');
					$sth->execute($retweet_id);
					my $data = $sth->fetchall_arrayref(+{});
					$tweet{'RERETWEET_MESSAGE'} = 'Retweet '.$data->[0]->{'mail'}.'\'s tweet';
				}

				push @tweets, \%tweet;
			}
			$tweet{'RETWEET_LOOP'} = \@tweets;
		}

		# Push tweet
		push @tweets, \%tweet;
	}
	$timeline_tmpl->param('TIMELINE_LOOP' => \@tweets);

	# Pager
	if($tweet_count == 0){
		$timeline_tmpl->param(IS_TWEET_EMPTY => 1);
	}else{
		my $current_page_num = $page;
		my $total_page_num = ceil($tweet_count / 15);
		$timeline_tmpl->param('PREV_PAGE_HREF' => $current_page_num == 1               ? '' : '<a href="?page='.($current_page_num-1).'"><span class="glyphicon glyphicon-chevron-left"></span> 前のページ</a>');
		$timeline_tmpl->param('NEXT_PAGE_HREF' => $current_page_num == $total_page_num ? '' : '<a href="?page='.($current_page_num+1).'">次のページ <span class="glyphicon glyphicon-chevron-right"></span></a>');
		$timeline_tmpl->param('CURRENT_PAGE_NUMBER' => $current_page_num);
		$timeline_tmpl->param('TOTAL_PAGE_NUMBER' => $total_page_num);
	}

	return $timeline_tmpl;
}

1;
